"""
Сервис парсинга Instagram через ScrapeCreators API.
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from loguru import logger

from app.config import get_config, Config
from app.models import OriginalPost, PostStatus, get_session
from app.services.author_manager import AuthorManager
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


class InstagramParser:
    """Сервис парсинга Instagram через ScrapeCreators API."""

    def __init__(self, settings: Optional[Config] = None):
        """
        Инициализация парсера.

        Args:
            settings: Конфигурация (если None — используется get_config()).
        """
        self.settings = settings or get_config()

    async def parse_accounts(
        self,
        accounts: List[str],
        min_likes: Optional[int] = None,
        max_age_days: Optional[int] = None,
        posts_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Парсит Instagram аккаунты через ScrapeCreators API.

        Args:
            accounts: Список username'ов или URL для парсинга
            min_likes: Минимум лайков для фильтра (None — из config/.env)
            max_age_days: Максимальный возраст поста (None — из config/.env)
            posts_limit: Сколько постов парсить с каждого аккаунта

        Returns:
            Список постов в формате dict
        """
        logger.info(f"Starting Instagram parsing for {len(accounts)} accounts")

        try:
            all_posts = []
            for username in accounts:
                try:
                    clean_username = (username or "").strip().lstrip("@")
                    if not clean_username:
                        continue
                    if clean_username.startswith("http://") or clean_username.startswith("https://"):
                        clean_username = clean_username.rstrip("/").split("/")[-1] or clean_username
                    posts = await self._fetch_profile_posts(clean_username, posts_limit)
                    all_posts.extend(posts)
                except Exception as e:
                    logger.error(f"Error parsing @{username}: {e}")

            logger.info(f"Fetched {len(all_posts)} posts from ScrapeCreators")

            filtered = self.filter_viral_posts(
                all_posts,
                min_text_length=getattr(self.settings, "MIN_TEXT_LENGTH", 100),
                max_age_days=max_age_days if max_age_days is not None else getattr(self.settings, "MAX_POST_AGE_DAYS", 3),
                min_likes=min_likes if min_likes is not None else getattr(self.settings, "MIN_LIKES", 5000)
            )
            logger.info(f"Filtered to {len(filtered)} viral posts")
            return filtered

        except Exception as e:
            logger.error(f"Error parsing Instagram: {e}")
            raise

    async def _fetch_profile_posts(
        self, username: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Получить посты профиля через ScrapeCreators."""
        url = "https://api.scrapecreators.com/v1/instagram/profile"
        headers = {"x-api-key": self.settings.SCRAPECREATORS_API_KEY}
        params = {"handle": username.replace("@", "")}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if not data.get("success"):
                    raise Exception(f"API error: {data}")

                # Извлечь посты из edge_felix_video_timeline (видео)
                posts_data = (
                    data.get("data", {})
                    .get("edge_felix_video_timeline", {})
                    .get("edges", [])
                )

                # Дополнительно: edge_owner_to_timeline_media (фото + видео)
                if not posts_data:
                    posts_data = (
                        data.get("data", {})
                        .get("edge_owner_to_timeline_media", {})
                        .get("edges", [])
                    )

                posts = []
                for edge in posts_data[:limit]:
                    node = edge.get("node", {})

                    # Извлечь caption
                    caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                    if caption_edges:
                        caption = caption_edges[0].get("node", {}).get("text", "")
                    else:
                        caption = ""

                    shortcode = node.get("shortcode") or node.get("id", "")
                    taken_at = node.get("taken_at_timestamp")
                    if taken_at:
                        timestamp_str = datetime.utcfromtimestamp(taken_at).strftime("%Y-%m-%dT%H:%M:%S+00:00")
                    else:
                        timestamp_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

                    post = {
                        "id": shortcode,
                        "shortCode": shortcode,
                        "ownerUsername": username,
                        "caption": caption,
                        "likesCount": node.get("edge_liked_by", {}).get("count", 0),
                        "commentsCount": node.get("edge_media_to_comment", {}).get("count", 0),
                        "timestamp": timestamp_str,
                        "url": f"https://www.instagram.com/p/{shortcode}/",
                        "is_video": node.get("is_video", False),
                        "display_url": node.get("display_url"),
                        "video_url": node.get("video_url") if node.get("is_video") else None,
                    }
                    posts.append(post)

                logger.info(f"Fetched {len(posts)} posts from @{username}")
                return posts

    def filter_viral_posts(
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
                shortcode = post.get("shortCode") or post.get("id", "?")
                likes = post.get("likesCount", 0)
                age_days: Optional[float] = None

                required = ["id", "ownerUsername", "caption", "likesCount"]
                if not all(k in post for k in required):
                    missing = [k for k in required if k not in post]
                    logger.debug(
                        f"Post {shortcode} filtered out: missing required fields {missing}"
                    )
                    continue

                if likes < min_likes:
                    logger.debug(
                        f"Post {shortcode} filtered out: likes={likes} (min={min_likes})"
                    )
                    continue

                timestamp = post.get("timestamp")
                if timestamp:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    post_date_naive = post_date.replace(tzinfo=None) if post_date.tzinfo else post_date
                    now = datetime.utcnow()
                    age_days = (now - post_date_naive).days
                    if post_date_naive < cutoff_date:
                        logger.debug(
                            f"Post {shortcode} filtered out: age_days={age_days} (max={max_age_days})"
                        )
                        continue
                else:
                    age_days = None
                    logger.debug(f"Post {shortcode}: no timestamp (passing age check)")

                caption = post.get("caption", "")
                if len(caption) < min_text_length:
                    logger.debug(
                        f"Post {shortcode} filtered out: caption_len={len(caption)} (min={min_text_length})"
                    )
                    continue

                logger.info(
                    f"Post {shortcode} passed filter: likes={likes}, age_days={age_days}"
                )
                filtered.append(post)

            except Exception as e:
                logger.warning(f"Error filtering post {post.get('id')}: {e}")
                continue

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
                shortcode = post.get("shortCode") or post.get("id", "?")
                likes = post.get("likesCount", 0)

                if not all(k in post for k in ["id", "ownerUsername", "caption", "likesCount"]):
                    missing = [k for k in ["id", "ownerUsername", "caption", "likesCount"] if k not in post]
                    logger.debug(f"Post {shortcode} filtered out: missing fields {missing}")
                    continue
                username = (post.get("ownerUsername") or "").strip().lower()
                settings = author_settings_map.get(username)
                if not settings:
                    logger.debug(f"Post {shortcode} filtered out: no settings for @{username}")
                    continue
                min_likes, max_age_days = settings
                cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

                if likes < min_likes:
                    logger.debug(
                        f"Post {shortcode} filtered out: likes={likes} (min={min_likes})"
                    )
                    continue

                age_days: Optional[float] = None
                timestamp = post.get("timestamp")
                if timestamp:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    post_date_naive = post_date.replace(tzinfo=None) if post_date.tzinfo else post_date
                    if post_date.tzinfo:
                        age_days = (datetime.now(post_date.tzinfo) - post_date).days
                    else:
                        age_days = (datetime.utcnow() - post_date).days
                    if post_date_naive < cutoff_date:
                        logger.debug(
                            f"Post {shortcode} filtered out: age_days={age_days} (max={max_age_days})"
                        )
                        continue
                else:
                    age_days = None
                    logger.debug(f"Post {shortcode}: no timestamp (passing age check)")

                caption = post.get("caption", "")
                if len(caption) < min_text_length:
                    logger.debug(
                        f"Post {shortcode} filtered out: caption_len={len(caption)} (min={min_text_length})"
                    )
                    continue

                logger.info(
                    f"Post {shortcode} passed filter: likes={likes}, age_days={age_days}"
                )
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

        all_posts = []
        for username in accounts:
            try:
                clean_username = (username or "").strip().lstrip("@")
                if not clean_username:
                    continue
                posts = await self._fetch_profile_posts(clean_username, posts_limit)
                all_posts.extend(posts)
            except Exception as e:
                logger.error(f"Error parsing @{username}: {e}")

        logger.info(f"Fetched {len(all_posts)} posts from ScrapeCreators")

        filtered = self.filter_viral_posts_per_author(
            all_posts,
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
                    external_id = post_data.get("id") or post_data.get("shortCode", "")
                    if not external_id:
                        continue

                    result = await session.execute(
                        select(OriginalPost).where(OriginalPost.external_id == external_id)
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        logger.debug(f"Post {external_id} already exists, skipping")
                        continue

                    timestamp = post_data.get("timestamp")
                    posted_at = (
                        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if timestamp
                        else datetime.utcnow()
                    )

                    new_post = OriginalPost(
                        external_id=external_id,
                        author=post_data["ownerUsername"],
                        author_url=f"https://www.instagram.com/{post_data['ownerUsername']}/",
                        text=post_data.get("caption", post_data.get("text", "")),
                        likes=post_data.get("likesCount", post_data.get("likes", 0)),
                        comments=post_data.get("commentsCount", post_data.get("comments", 0)),
                        engagement=0.0,
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
        posts = await parser.parse_accounts(
            accounts=config.instagram_authors_list[:3],
            min_likes=config.MIN_LIKES,
            max_age_days=config.MAX_POST_AGE_DAYS,
            posts_limit=5
        )

        print(f"\n✅ Found {len(posts)} viral posts")

        saved = await parser.save_to_db(posts)
        print(f"💾 Saved {len(saved)} posts to database")

        for post in saved[:3]:
            print(f"\n📝 @{post.author}: {post.likes} likes")
            print(f"   {post.text[:100]}...")

    finally:
        pass


if __name__ == "__main__":
    from app.utils.logger import setup_logger
    setup_logger()
    asyncio.run(main())
