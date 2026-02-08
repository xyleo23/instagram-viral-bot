"""
Сервис публикации каруселей в Instagram через Instagrapi.
Загружает сессию из файла, при ошибке логинится заново.
Обновляет статусы: PUBLISHING → PUBLISHED или FAILED.
"""
import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    BadPassword,
    TwoFactorRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import async_session_maker
from app.models.processed_post import ProcessedPost


MOSCOW_TZ = ZoneInfo("Europe/Moscow")
MAX_CAROUSEL_SLIDES = 10
SESSION_DIR = Path("sessions")


class InstagramPublisher:
    """
    Публикует карусели в Instagram через Instagrapi.
    Использует сохранённую сессию для избежания повторных логинов.
    """

    def __init__(
        self,
        username: str,
        password: str,
        proxy: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.proxy = proxy
        self._client: Optional[Client] = None
        self._session_path = SESSION_DIR / f"session_{username}.json"

    def _get_client(self) -> Client:
        """Возвращает или создаёт экземпляр Instagrapi Client."""
        if self._client is None:
            self._client = Client()
            # Задержки между запросами (мл/с) — имитация реального пользователя
            self._client.delay_range = [1000, 3000]
            if self.proxy:
                logger.info(f"[Instagram] Using proxy: {self.proxy[:30]}...")
                self._client.set_proxy(self.proxy)
        return self._client

    async def login(self) -> bool:
        """
        Авторизация: загружает сессию из файла, при необходимости логинится.
        Возвращает True при успехе.
        """
        def _do_login() -> bool:
            cl = self._get_client()
            SESSION_DIR.mkdir(parents=True, exist_ok=True)

            # Попытка загрузить сессию
            if self._session_path.exists():
                try:
                    logger.info(f"[Instagram] Loading session from {self._session_path}")
                    session = cl.load_settings(str(self._session_path))
                    if session:
                        cl.set_settings(session)
                        cl.login(self.username, self.password)
                        cl.get_timeline_feed()  # проверка валидности сессии
                        logger.info(f"[Instagram] Session valid for {self.username}")
                        return True
                except (LoginRequired, ChallengeRequired) as e:
                    logger.warning(f"[Instagram] Session expired or challenge: {e}")
                except Exception as e:
                    logger.warning(f"[Instagram] Session load failed: {e}")

            # Свежий логин
            logger.info(f"[Instagram] Logging in as {self.username}")
            cl.login(self.username, self.password)
            cl.dump_settings(str(self._session_path))
            logger.info(f"[Instagram] Session saved to {self._session_path}")
            return True

        try:
            return await asyncio.to_thread(_do_login)
        except (BadPassword, TwoFactorRequired) as e:
            logger.error(f"[Instagram] Auth failed: {e}")
            raise
        except Exception as e:
            logger.exception(f"[Instagram] Login error: {e}")
            raise

    def _upload_carousel(self, paths: List[Path], caption: str) -> str:
        """
        Загрузка карусели через Instagrapi (синхронно).
        Возвращает instagram_post_id (pk как строка).
        """
        cl = self._get_client()
        if not cl.user_id:
            raise LoginRequired("Not logged in")

        paths = paths[:MAX_CAROUSEL_SLIDES]
        media = cl.album_upload(paths, caption)
        return str(media.pk)

    async def publish_carousel(
        self,
        post_id: int,
        image_paths: List[str],
        caption: str,
        hashtags: str = "",
    ) -> Optional[str]:
        """
        Публикует карусель в Instagram.

        Args:
            post_id: ID ProcessedPost
            image_paths: Список путей к изображениям слайдов
            caption: Текст поста (caption + hashtags)
            hashtags: Хештеги (включаются в caption)

        Returns:
            instagram_post_id при успехе, None при ошибке
        """
        logger.info(f"[Instagram] publish_carousel: post_id={post_id}, slides={len(image_paths)}")

        full_caption = f"{caption}\n\n{hashtags}".strip() if hashtags else caption

        async with async_session_maker() as session:
            async with session.begin():
                await self._set_status(session, post_id, "PUBLISHING")

        try:
            await self.login()

            path_objs = [Path(p) for p in image_paths[:MAX_CAROUSEL_SLIDES]]
            for p in path_objs:
                if not p.exists():
                    raise FileNotFoundError(f"Image not found: {p}")

            instagram_post_id = await asyncio.to_thread(
                self._upload_carousel,
                path_objs,
                full_caption,
            )

            async with async_session_maker() as session:
                async with session.begin():
                    await self._set_published(session, post_id, instagram_post_id)

            logger.info(f"[Instagram] Post {post_id} published: instagram_post_id={instagram_post_id}")
            return instagram_post_id

        except (PleaseWaitFewMinutes, RateLimitError) as e:
            err_msg = f"Rate limit / wait: {e}"
            logger.warning(f"[Instagram] {err_msg}")
            await self.mark_failed(post_id, err_msg)
            return None
        except (LoginRequired, ChallengeRequired) as e:
            err_msg = f"Session/challenge: {e}"
            logger.error(f"[Instagram] {err_msg}")
            await self.mark_failed(post_id, err_msg)
            return None
        except Exception as e:
            err_msg = str(e)
            logger.exception(f"[Instagram] Publish failed for post {post_id}: {e}")
            await self.mark_failed(post_id, err_msg)
            return None

    async def mark_failed(self, post_id: int, error_message: str) -> None:
        """Устанавливает статус FAILED и сохраняет текст ошибки."""
        logger.error(f"[Instagram] Marking post {post_id} as FAILED: {error_message}")

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
        logger.debug(f"[Instagram] Post {post_id} status -> {status}")

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


def _random_delay_minutes() -> float:
    """Случайная задержка 5–15 минут (в секундах)."""
    return random.uniform(5 * 60, 15 * 60)
