"""
Сервис парсинга Instagram через Apify API.
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from loguru import logger
import json

from app.config import get_config, Config
from app.models import OriginalPost, PostStatus, get_session
from app.services.author_manager import AuthorManager
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


def _normalize_start_urls(accounts: List[str]) -> List[str]:
    """Преобразует список username или URL в список startUrls."""
    urls = []
    for acc in accounts:
        acc = (acc or "").strip()
        if not acc:
            continue
        if acc.startswith("http://") or acc.startswith("https://"):
            urls.append(acc)
        else:
            urls.append(f"https://www.instagram.com/{acc}/")
    return urls


class InstagramParser:
    """Сервис парсинга Instagram через Apify API."""

    def __init__(self, settings: Optional[Config] = None):
        """
        Инициализация парсера.

        Args:
            settings: Конфигурация (если None — используется get_config()).
        """
        self.settings = settings or get_config()
        self._token = getattr(self.settings, "APIFY_TOKEN", None) or getattr(
            self.settings, "APIFY_API_KEY", ""
        )
        self._act_id = getattr(self.settings, "APIFY_INSTAGRAM_ACT_ID", "") or ""
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def parse_accounts(
        self,
        accounts: List[str],
        min_likes: int = 5000,
        max_age_days: int = 3,
        posts_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Парсит Instagram аккаунты через Apify.

        Args:
            accounts: Список username'ов или URL для парсинга
            min_likes: Минимум лайков для фильтра
            max_age_days: Максимальный возраст поста
            posts_limit: Сколько постов парсить с каждого аккаунта

        Returns:
            Список постов в формате dict
        """
        logger.info(f"Starting Instagram parsing for {len(accounts)} accounts")

        try:
            run_id = await self._start_apify_run(accounts, posts_limit)
            run_info = await self._wait_for_apify_run(run_id)
            dataset_id = run_info.get("data", {}).get("defaultDatasetId") or run_info.get("defaultDatasetId")
            if not dataset_id:
                raise ValueError("Apify run did not return defaultDatasetId")
            posts = await self._fetch_items_from_dataset(dataset_id)
            logger.info(f"Fetched {len(posts)} posts from Apify")

            filtered = await self.filter_viral_posts(
                posts,
                min_likes=min_likes,
                max_age_days=max_age_days
            )
            logger.info(f"Filtered to {len(filtered)} viral posts")
            return filtered

        except Exception as e:
            logger.error(f"Error parsing Instagram: {e}")
            raise

    async def _start_apify_run(
        self,
        accounts: List[str],
        posts_limit: int
    ) -> str:
        """
        Запускает Apify акт по URL:
        https://api.apify.com/v2/acts/{ACT_ID}/runs?token={TOKEN}

        Returns:
            Run ID
        """
        act_id = self._act_id
        token = self._token
        if not act_id or not token:
            raise ValueError("APIFY_INSTAGRAM_ACT_ID and APIFY_TOKEN must be set in settings")

        start_urls = _normalize_start_urls(accounts)
        payload = {
            "startUrls": start_urls,
            "maximumItems": posts_limit,
        }
        url = f"https://api.apify.com/v2/acts/{act_id}/runs?token={token}"

        logger.info(f"Starting Apify run for {len(accounts)} accounts via {act_id}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status not in (200, 201):
                        body = await resp.text()
                        logger.error(f"Apify start run failed: status={resp.status}, url={url}, body={body}")
                        resp.raise_for_status()
                    data = await resp.json()
            run_id = (data.get("data") or {}).get("id") or data.get("id")
            if not run_id:
                logger.error(f"Apify response missing run id: {data}")
                raise ValueError("Apify response missing run id")
            logger.info(f"Apify run started: run_id={run_id}")
            return str(run_id)
        except aiohttp.ClientError as e:
            logger.exception(f"Apify request error: url={url}, payload={payload}, error={e}")
            raise
        except Exception as e:
            logger.exception(f"Apify start run error: url={url}, payload={payload}, error={e}")
            raise

    async def _wait_for_apify_run(
        self,
        run_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Ждет завершения Apify run.
        URL: https://api.apify.com/v2/acts/{act_id}/runs/{run_id}?token={token}

        Returns:
            Полный ответ run (для получения defaultDatasetId).
        """
        act_id = self._act_id
        token = self._token
        url = f"https://api.apify.com/v2/acts/{act_id}/runs/{run_id}?token={token}"

        start_time = datetime.now()
        last_data: Dict[str, Any] = {}

        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    if (datetime.now() - start_time).total_seconds() > max_wait:
                        raise TimeoutError(f"Apify run {run_id} timeout after {max_wait}s")

                    async with session.get(url) as resp:
                        if resp.status != 200:
                            body = await resp.text()
                            logger.error(f"Apify run status failed: status={resp.status}, url={url}, body={body}")
                            resp.raise_for_status()
                        data = await resp.json()
                    last_data = data
                    status = (data.get("data") or {}).get("status") or data.get("status", "")

                    logger.debug(f"Apify run {run_id} status: {status}")

                    if status == "SUCCEEDED":
                        logger.info(f"Apify run {run_id} succeeded")
                        return data
                    if status in ("FAILED", "ABORTED", "TIMED-OUT", "TIMED_OUT"):
                        raise Exception(f"Apify run {run_id} failed with status: {status}")

                    await asyncio.sleep(poll_interval)
        except aiohttp.ClientError as e:
            logger.exception(f"Apify wait run request error: url={url}, error={e}")
            raise

    async def _fetch_items_from_dataset(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Получает элементы датасета по ID.
        GET https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}
        """
        token = self._token
        url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    items = await resp.json()
            logger.info(f"Fetched {len(items)} items from dataset {dataset_id}")
            return items if isinstance(items, list) else list(items)
        except aiohttp.ClientError as e:
            logger.exception(f"Apify dataset fetch error: url={url}, error={e}")
            raise

    async def _get_results(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Получает результаты Apify run через defaultDatasetId (для обратной совместимости).
        """
        run_info = await self._wait_for_apify_run(run_id)
        dataset_id = run_info.get("data", {}).get("defaultDatasetId") or run_info.get("defaultDatasetId")
        if not dataset_id:
            raise ValueError("Apify run did not return defaultDatasetId")
        return await self._fetch_items_from_dataset(dataset_id)
    
    async def filter_viral_posts(
        self,
        posts: List[Dict[str, Any]],
        min_likes: int = 5000,
        max_age_days: int = 3,
        min_text_length: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует только вирусные посты.
        
        Args:
            posts: Список постов
            min_likes: Минимум лайков
            max_age_days: Максимальный возраст
            min_text_length: Минимальная длина текста
        
        Returns:
            Отфильтрованные посты, отсортированные по лайкам
        """
        filtered = []
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        for post in posts:
            try:
                # Проверяем наличие обязательных полей
                if not all(k in post for k in ["id", "ownerUsername", "caption", "likesCount"]):
                    continue
                
                # Фильтруем по лайкам
                likes = post.get("likesCount", 0)
                if likes < min_likes:
                    continue
                
                # Фильтруем по возрасту
                timestamp = post.get("timestamp")
                if timestamp:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if post_date < cutoff_date:
                        continue
                
                # Фильтруем по длине текста
                caption = post.get("caption", "")
                if len(caption) < min_text_length:
                    continue
                
                # Пост прошел все фильтры
                filtered.append(post)
                
            except Exception as e:
                logger.warning(f"Error filtering post {post.get('id')}: {e}")
                continue
        
        # Сортируем по лайкам (по убыванию)
        filtered.sort(key=lambda x: x.get("likesCount", 0), reverse=True)
        
        return filtered

    def filter_viral_posts_per_author(
        self,
        posts: List[Dict[str, Any]],
        author_settings_map: Dict[str, Tuple[int, int]],
        min_text_length: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует посты по персональным настройкам авторов.
        author_settings_map: username -> (min_likes, max_age_days)
        """
        filtered = []
        for post in posts:
            try:
                if not all(k in post for k in ["id", "ownerUsername", "caption", "likesCount"]):
                    continue
                username = (post.get("ownerUsername") or "").strip().lower()
                settings = author_settings_map.get(username)
                if not settings:
                    logger.debug(f"No settings for @{username}, skipping post")
                    continue
                min_likes, max_age_days = settings
                cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
                likes = post.get("likesCount", 0)
                if likes < min_likes:
                    continue
                timestamp = post.get("timestamp")
                if timestamp:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if post_date < cutoff_date:
                        continue
                caption = post.get("caption", "")
                if len(caption) < min_text_length:
                    continue
                filtered.append(post)
            except Exception as e:
                logger.warning(f"Error filtering post {post.get('id')}: {e}")
        filtered.sort(key=lambda x: x.get("likesCount", 0), reverse=True)
        return filtered

    async def parse_accounts_with_settings(
        self,
        posts_limit: int = 10,
        fallback_min_likes: Optional[int] = None,
        fallback_max_age_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Парсит только активных авторов из AuthorManager с персональными настройками.
        Если активных авторов нет — использует config (instagram_authors_list, MIN_LIKES, MAX_POST_AGE_DAYS).
        """
        authors = await AuthorManager.get_active_authors()
        config = get_config()
        if not authors:
            logger.info("No active authors in DB, using config list and defaults")
            accounts = config.instagram_authors_list
            min_likes = fallback_min_likes if fallback_min_likes is not None else config.MIN_LIKES
            max_age_days = fallback_max_age_days if fallback_max_age_days is not None else config.MAX_POST_AGE_DAYS
            return await self.parse_accounts(
                accounts=accounts,
                min_likes=min_likes,
                max_age_days=max_age_days,
                posts_limit=posts_limit,
            )
        accounts = [a.username for a in authors]
        author_settings_map = {
            a.username: (a.min_likes, a.max_post_age_days) for a in authors
        }
        logger.info(f"Parsing {len(accounts)} active authors with per-author settings")
        run_id = await self._start_apify_run(accounts, posts_limit)
        run_info = await self._wait_for_apify_run(run_id)
        dataset_id = run_info.get("data", {}).get("defaultDatasetId") or run_info.get("defaultDatasetId")
        if not dataset_id:
            raise ValueError("Apify run did not return defaultDatasetId")
        posts = await self._fetch_items_from_dataset(dataset_id)
        logger.info(f"Fetched {len(posts)} posts from Apify")
        filtered = self.filter_viral_posts_per_author(
            posts,
            author_settings_map=author_settings_map,
            min_text_length=config.MIN_TEXT_LENGTH,
        )
        logger.info(f"Filtered to {len(filtered)} viral posts (per-author settings)")
        return filtered

    async def save_to_db(
        self,
        posts: List[Dict[str, Any]],
        status: PostStatus = PostStatus.FILTERED
    ) -> List[OriginalPost]:
        """
        Сохраняет посты в БД.
        
        Args:
            posts: Список постов
            status: Начальный статус
        
        Returns:
            Список сохраненных моделей
        """
        saved_posts = []
        
        async with get_session() as session:
            for post_data in posts:
                try:
                    # Проверяем существование по external_id
                    external_id = post_data["id"]
                    
                    result = await session.execute(
                        select(OriginalPost).where(OriginalPost.external_id == external_id)
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        logger.debug(f"Post {external_id} already exists, skipping")
                        continue
                    
                    # Парсим дату
                    timestamp = post_data.get("timestamp")
                    posted_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else datetime.utcnow()
                    
                    # Создаем новый пост
                    new_post = OriginalPost(
                        external_id=external_id,
                        author=post_data["ownerUsername"],
                        author_url=f"https://www.instagram.com/{post_data['ownerUsername']}/",
                        text=post_data.get("caption", ""),
                        likes=post_data.get("likesCount", 0),
                        comments=post_data.get("commentsCount", 0),
                        engagement=0.0,  # TODO: посчитать если есть данные о подписчиках
                        post_url=post_data.get("url", f"https://www.instagram.com/p/{external_id}/"),
                        posted_at=posted_at,
                        status=status
                    )
                    
                    session.add(new_post)
                    await session.flush()
                    
                    saved_posts.append(new_post)
                    logger.info(f"Saved post {external_id} from @{new_post.author}")
                    
                except IntegrityError:
                    logger.warning(f"Duplicate post {post_data.get('id')}, skipping")
                    await session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error saving post {post_data.get('id')}: {e}")
                    await session.rollback()
                    continue
            
            await session.commit()
        
        logger.info(f"Saved {len(saved_posts)} new posts to database")
        return saved_posts


# ==================== USAGE EXAMPLE ====================

async def main():
    """Пример использования."""
    config = get_config()
    parser = InstagramParser(settings=config)
    
    try:
        # Парсинг
        posts = await parser.parse_accounts(
            accounts=config.instagram_authors_list[:3],  # Первые 3 автора для теста
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=5
        )
        
        print(f"\n✅ Found {len(posts)} viral posts")
        
        # Сохранение в БД
        saved = await parser.save_to_db(posts)
        print(f"💾 Saved {len(saved)} posts to database")
        
        # Вывод
        for post in saved[:3]:
            print(f"\n📝 @{post.author}: {post.likes} likes")
            print(f"   {post.text[:100]}...")
        
    finally:
        await parser.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
