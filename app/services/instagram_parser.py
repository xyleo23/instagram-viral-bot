"""
Сервис парсинга Instagram через Instaloader.
"""
import instaloader
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from loguru import logger

from app.config import get_config, Config
from app.models import OriginalPost, PostStatus, get_session
from app.services.author_manager import AuthorManager
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


def _fetch_profile_posts_sync(context, username: str, limit: int) -> List[Dict[str, Any]]:
    """Синхронно получает посты профиля (для запуска в executor)."""
    clean_username = username.replace("@", "").strip()
    profile = instaloader.Profile.from_username(context, clean_username)
    posts = []
    for i, post in enumerate(profile.get_posts()):
        if len(posts) >= limit:
            break
        if i > 0:
            time.sleep(3)
        is_carousel = getattr(post, "typename", None) == "GraphSidecar"
        carousel_count = 0
        if is_carousel:
            try:
                carousel_count = len(list(post.get_sidecar_nodes()))
            except Exception:
                pass
        timestamp_iso = post.date_utc.strftime("%Y-%m-%dT%H:%M:%S+00:00") if post.date_utc else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        post_data = {
            "id": post.shortcode,
            "shortCode": post.shortcode,
            "ownerUsername": clean_username,
            "caption": (post.caption or "") or "",
            "likesCount": post.likes,
            "commentsCount": post.comments,
            "timestamp": timestamp_iso,
            "url": f"https://www.instagram.com/p/{post.shortcode}/",
            "is_video": getattr(post, "is_video", False),
            "display_url": getattr(post, "url", None) or (post.url if hasattr(post, "url") else None),
            "video_url": getattr(post, "video_url", None) if getattr(post, "is_video", False) else None,
        }
        posts.append(post_data)
    return posts


class InstagramParser:
    """Сервис парсинга Instagram через Instaloader."""

    def __init__(self, settings: Optional[Config] = None):
        self.settings = settings or get_config()
        self.loader = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
        )
        self._logged_in = False

    async def login(self) -> None:
        """Логин в Instagram через Instaloader."""
        if self._logged_in:
            return
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.loader.login,
                self.settings.INSTAGRAM_PARSER_USERNAME,
                self.settings.INSTAGRAM_PARSER_PASSWORD,
            )
            self._logged_in = True
            logger.info("Successfully logged in to Instagram")
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {e}")
            raise

    async def close(self) -> None:
        """Закрытие парсера (no-op для Instaloader)."""
        pass

    async def parse_accounts(
        self,
        accounts: List[str],
        min_likes: Optional[int] = None,
        max_age_days: Optional[int] = None,
        posts_limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Парсит Instagram аккаунты через Instaloader."""
        await self.login()
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

        logger.info(f"Fetched {len(all_posts)} posts from Instaloader")

        min_likes_val = min_likes if min_likes is not None else getattr(self.settings, "MIN_LIKES", 5000)
        max_age_val = max_age_days if max_age_days is not None else getattr(self.settings, "MAX_POST_AGE_DAYS", 3)
        min_text = getattr(self.settings, "MIN_TEXT_LENGTH", 100)

        viral_posts = self.filter_viral_posts(
            all_posts,
            min_likes=min_likes_val,
            max_age_days=max_age_val,
            min_text_length=min_text,
        )
        logger.info(f"Filtered to {len(viral_posts)} viral posts")
        return viral_posts

    async def _fetch_profile_posts(self, username: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить посты профиля через Instaloader."""
        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(
            None,
            _fetch_profile_posts_sync,
            self.loader.context,
            username.replace("@", "").strip(),
            limit,
        )
        logger.info(f"Fetched {len(posts)} posts from @{username}")
        return posts

    def filter_viral_posts(
        self,
        posts: List[Dict[str, Any]],
        min_likes: int = 5000,
        max_age_days: int = 3,
        min_text_length: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует только вирусные посты.
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
        """
        await self.login()
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

        logger.info(f"Fetched {len(all_posts)} posts from Instaloader")

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
        status: PostStatus = PostStatus.FILTERED,
    ) -> List[OriginalPost]:
        """
        Сохраняет посты в БД.
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
                        status=status,
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
            posts_limit=5,
        )

        print(f"\n✅ Found {len(posts)} viral posts")

        for post in posts[:3]:
            print(f"\n📝 @{post.get('ownerUsername')}: {post.get('likesCount')} likes")
            print(f"   {(post.get('caption') or '')[:100]}...")
    finally:
        await parser.close()


if __name__ == "__main__":
    from app.utils.logger import setup_logger

    setup_logger()
    asyncio.run(main())
