"""
Фоновый планировщик для автоматической публикации постов в Instagram.
Проверяет запланированные посты каждую минуту и публикует по расписанию.
Использует Instagrapi для реальной публикации.
"""
import asyncio
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.models import get_session
from app.models.processed_post import ProcessedPost
from app.services.image_generator import ImageGenerator
from app.services.instagram_publisher import (
    InstagramPublisher,
    _random_delay_minutes,
)


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class PostScheduler:
    """
    Фоновый планировщик публикаций.
    Запускается вместе с ботом, проверяет посты каждую минуту.
    """

    def __init__(self) -> None:
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 60  # секунды
        self._image_generator = ImageGenerator()
        config = get_config()
        self._publisher = InstagramPublisher(
            username=config.INSTAGRAM_USERNAME or "",
            password=config.INSTAGRAM_PASSWORD or "",
            proxy=config.INSTAGRAM_PROXY,
        )

    async def start(self) -> None:
        """Запускает фоновую проверку постов."""
        if self._running:
            logger.warning("PostScheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PostScheduler started (check every 60s, timezone=Europe/Moscow)")

    async def stop(self) -> None:
        """Останавливает планировщик (graceful shutdown)."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("PostScheduler stopped")

    async def _run_loop(self) -> None:
        """Основной цикл проверки."""
        while self._running:
            try:
                await self.check_scheduled_posts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"PostScheduler error: {e}")

            try:
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break

    async def check_scheduled_posts(self) -> None:
        """
        Проверяет посты, запланированные на публикацию.
        Находит посты со статусом SCHEDULED и scheduled_at <= now (Europe/Moscow).
        """
        now_moscow = datetime.now(MOSCOW_TZ)
        logger.debug(f"Checking scheduled posts at {now_moscow.isoformat()}")

        async with get_session() as session:
            stmt = select(ProcessedPost).where(
                and_(
                    ProcessedPost.publication_status == "SCHEDULED",
                    ProcessedPost.scheduled_at <= now_moscow,
                )
            )
            result = await session.execute(stmt)
            posts = result.scalars().all()
            break

        if not posts:
            return

        config = get_config()
        if not (config.INSTAGRAM_USERNAME and config.INSTAGRAM_PASSWORD):
            logger.warning("INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD not set, skipping publish")
            return

        logger.info(f"Found {len(posts)} post(s) ready for publishing")
        for idx, post in enumerate(posts):
            if idx > 0:
                delay_sec = _random_delay_minutes()
                logger.info(f"Delay {delay_sec / 60:.1f} min before next post (anti rate-limit)")
                await asyncio.sleep(delay_sec)
            try:
                await self.publish_post(post)
            except Exception as e:
                logger.exception(f"Failed to publish post {post.id}: {e}")

    async def publish_post(self, post: ProcessedPost) -> None:
        """
        Запускает публикацию поста: генерация изображений → публикация карусели.
        """
        post_id = post.id
        logger.info(f"Publishing post {post_id}")

        try:
            image_paths = await self._image_generator.generate_slide_images(post_id)
            if not image_paths:
                raise ValueError("No images generated")

            caption = f"{post.title}\n\n{post.caption}".strip()
            hashtags = post.hashtags or ""
            instagram_post_id = await self._publisher.publish_carousel(
                post_id=post_id,
                image_paths=image_paths,
                caption=caption,
                hashtags=hashtags,
            )
            if instagram_post_id:
                logger.info(f"Post {post_id} published successfully: instagram_post_id={instagram_post_id}")
            else:
                logger.warning(f"Post {post_id} publish returned None (marked FAILED)")
        except Exception as e:
            logger.error(f"Publish failed for post {post_id}: {e}")
            await self._publisher.mark_failed(post_id, str(e))
            raise
