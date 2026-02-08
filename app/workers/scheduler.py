"""
Фоновый планировщик для автоматической публикации постов в Instagram.
Проверяет запланированные посты каждую минуту и публикует по расписанию.
"""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.processed_post import ProcessedPost
from app.services.image_generator import ImageGenerator
from app.services.instagram_publisher import InstagramPublisher


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
        self._publisher = InstagramPublisher()

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

        async for session in get_session():
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

        logger.info(f"Found {len(posts)} post(s) ready for publishing")
        for post in posts:
            try:
                await self.publish_post(post.id)
            except Exception as e:
                logger.exception(f"Failed to publish post {post.id}: {e}")

    async def publish_post(self, post_id: int) -> None:
        """
        Запускает публикацию поста: генерация изображений → публикация карусели.
        """
        logger.info(f"Publishing post {post_id}")

        try:
            image_paths = await self._image_generator.generate_slide_images(post_id)
            if not image_paths:
                raise ValueError("No images generated")

            await self._publisher.publish_carousel(post_id, image_paths)
            logger.info(f"Post {post_id} published successfully")
        except Exception as e:
            logger.error(f"Publish failed for post {post_id}: {e}")
            await self._publisher.mark_failed(post_id, str(e))
            raise
