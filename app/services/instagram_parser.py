"""
Сервис парсинга Instagram через Apify API.
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from loguru import logger
import json

from app.config import get_config
from app.models import OriginalPost, PostStatus, get_session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


class InstagramParser:
    """Сервис парсинга Instagram через Apify API."""
    
    def __init__(self, api_key: str):
        """
        Инициализация парсера.
        
        Args:
            api_key: Apify API ключ
        """
        self.api_key = api_key
        self.base_url = "https://api.apify.com/v2"
        self.actor_id = "apify/instagram-scraper"  # ID актера Apify
        
        # HTTP сессия
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 минут
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
            accounts: Список username'ов для парсинга
            min_likes: Минимум лайков для фильтра
            max_age_days: Максимальный возраст поста
            posts_limit: Сколько постов парсить с каждого аккаунта
        
        Returns:
            Список постов в формате dict
        """
        logger.info(f"Starting Instagram parsing for {len(accounts)} accounts")
        
        try:
            # 1. Запустить Apify актер
            run_id = await self._start_apify_run(accounts, posts_limit)
            logger.info(f"Apify run started: {run_id}")
            
            # 2. Дождаться завершения
            await self._wait_for_run(run_id)
            
            # 3. Получить результаты
            posts = await self._get_results(run_id)
            logger.info(f"Fetched {len(posts)} posts from Apify")
            
            # 4. Фильтровать по критериям
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
        Запускает Apify актер.
        
        Returns:
            Run ID
        """
        session = await self._get_session()
        
        # Формируем input для актера
        actor_input = {
            "directUrls": [f"https://www.instagram.com/{acc}/" for acc in accounts],
            "resultsType": "posts",
            "resultsLimit": posts_limit,
            "searchType": "user",
            "searchLimit": 1,
            "addParentData": False
        }
        
        url = f"{self.base_url}/acts/{self.actor_id}/runs"
        params = {"token": self.api_key}
        
        async with session.post(url, params=params, json=actor_input) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["data"]["id"]
    
    async def _wait_for_run(
        self,
        run_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> None:
        """
        Ждет завершения Apify run.
        
        Args:
            run_id: ID запуска
            max_wait: Максимальное время ожидания в секундах
            poll_interval: Интервал проверки статуса
        """
        session = await self._get_session()
        url = f"{self.base_url}/actor-runs/{run_id}"
        params = {"token": self.api_key}
        
        start_time = datetime.now()
        
        while True:
            # Проверяем timeout
            if (datetime.now() - start_time).total_seconds() > max_wait:
                raise TimeoutError(f"Apify run {run_id} timeout after {max_wait}s")
            
            # Проверяем статус
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                status = data["data"]["status"]
                
                logger.debug(f"Apify run {run_id} status: {status}")
                
                if status == "SUCCEEDED":
                    logger.info(f"Apify run {run_id} succeeded")
                    return
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    raise Exception(f"Apify run {run_id} failed with status: {status}")
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(poll_interval)
    
    async def _get_results(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Получает результаты Apify run.
        
        Args:
            run_id: ID запуска
        
        Returns:
            Список постов
        """
        session = await self._get_session()
        url = f"{self.base_url}/actor-runs/{run_id}/dataset/items"
        params = {"token": self.api_key}
        
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            posts = await resp.json()
            return posts
    
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
        
        async for session in get_session():
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
    
    parser = InstagramParser(api_key=config.APIFY_API_KEY)
    
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
