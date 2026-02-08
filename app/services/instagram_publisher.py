"""
Сервис публикации каруселей в Instagram.
Пока заглушка с логированием — реальный API добавим позже.
Обновляет статусы: PUBLISHING → PUBLISHED или FAILED.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import List

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import async_session_maker
from app.models.processed_post import ProcessedPost


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class InstagramPublisher:
    """
    Публикует карусели в Instagram.
    Заглушка: логирует действия, обновляет статусы в БД.
    """

    async def publish_carousel(
        self,
        post_id: int,
        image_paths: List[str],
    ) -> None:
        """
        Публикует карусель в Instagram.

        Args:
            post_id: ID ProcessedPost
            image_paths: Список путей к изображениям слайдов
        """
        logger.info(f"[STUB] publish_carousel: post_id={post_id}, images={len(image_paths)}")

        async with async_session_maker() as session:
            async with session.begin():
                await self._set_status(session, post_id, "PUBLISHING")

            # Заглушка: вместо реального API — логирование
            # TODO: Instagram Graph API / instagrapi
            for idx, path in enumerate(image_paths):
                logger.debug(f"  Slide {idx + 1}: {path}")

            async with async_session_maker() as session:
                async with session.begin():
                    await self._set_published(session, post_id, "stub_instagram_id_123")

        logger.info(f"Post {post_id} marked as PUBLISHED (stub)")

    async def mark_failed(self, post_id: int, error_message: str) -> None:
        """Устанавливает статус FAILED и сохраняет текст ошибки."""
        logger.error(f"Marking post {post_id} as FAILED: {error_message}")

        async with async_session_maker() as session:
            async with session.begin():
                stmt = (
                    update(ProcessedPost)
                    .where(ProcessedPost.id == post_id)
                    .values(
                        publication_status="FAILED",
                        publication_error=error_message[:1000],
                    )
                )
                await session.execute(stmt)

    async def _set_status(
        self,
        session: AsyncSession,
        post_id: int,
        status: str,
    ) -> None:
        """Обновляет publication_status в транзакции."""
        stmt = (
            update(ProcessedPost)
            .where(ProcessedPost.id == post_id)
            .values(publication_status=status)
        )
        await session.execute(stmt)
        logger.debug(f"Post {post_id} status -> {status}")

    async def _set_published(
        self,
        session: AsyncSession,
        post_id: int,
        instagram_post_id: str,
    ) -> None:
        """Обновляет статус на PUBLISHED с instagram_post_id и published_at."""
        now = datetime.now(MOSCOW_TZ)
        stmt = (
            update(ProcessedPost)
            .where(ProcessedPost.id == post_id)
            .values(
                publication_status="PUBLISHED",
                instagram_post_id=instagram_post_id,
                published_at=now,
            )
        )
        await session.execute(stmt)
