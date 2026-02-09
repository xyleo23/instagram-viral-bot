"""
Сервис управления настройками авторов Instagram.
"""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import get_session, User, AuthorSettings


# Валидация
MIN_LIKES_LOWER = 100
MAX_AGE_DAYS_MIN = 1
MAX_AGE_DAYS_MAX = 30


def _validate_min_likes(value: int) -> int:
    if value < MIN_LIKES_LOWER:
        raise ValueError(f"min_likes должен быть не меньше {MIN_LIKES_LOWER}")
    return value


def _validate_max_age_days(value: int) -> int:
    if not (MAX_AGE_DAYS_MIN <= value <= MAX_AGE_DAYS_MAX):
        raise ValueError(f"max_post_age_days должен быть от {MAX_AGE_DAYS_MIN} до {MAX_AGE_DAYS_MAX}")
    return value


async def get_or_create_user_by_telegram_id(
    telegram_id: int,
    username: Optional[str] = None,
    session: Optional[AsyncSession] = None,
) -> User:
    """
    Возвращает пользователя по Telegram ID или создаёт нового.

    Args:
        telegram_id: Telegram User ID
        username: Telegram username (опционально)
        session: Опциональная сессия БД (если не передана — создаётся своя).

    Returns:
        User с заполненным id после flush при создании.
    """
    async def _run(sess: AsyncSession) -> User:
        result = await sess.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            if username and user.username != username:
                user.username = username
            return user
        new_user = User(telegram_id=telegram_id, username=username)
        sess.add(new_user)
        await sess.flush()
        logger.info(f"Created user id={new_user.id} telegram_id={telegram_id}")
        return new_user

    if session is not None:
        return await _run(session)

    async for sess in get_session():
        return await _run(sess)
    raise RuntimeError("get_session did not yield session")


class AuthorManager:
    """Управление настройками авторов Instagram."""

    @staticmethod
    async def add_author(
        username: str,
        admin_telegram_id: int,
        admin_username: Optional[str] = None,
        min_likes: int = 1000,
        max_age_days: int = 3,
    ) -> AuthorSettings:
        """
        Добавляет автора с настройками.

        Args:
            username: Instagram username (без @)
            admin_telegram_id: Telegram ID админа
            admin_username: Telegram username админа (опционально)
            min_likes: Минимум лайков (default 1000)
            max_age_days: Максимальный возраст поста в днях (default 3)

        Returns:
            AuthorSettings

        Raises:
            ValueError: при невалидных min_likes или max_age_days
            IntegrityError: если автор с таким username уже есть
        """
        username = username.strip().replace("@", "").lower()
        if not username:
            raise ValueError("username не может быть пустым")

        min_likes = _validate_min_likes(min_likes)
        max_age_days = _validate_max_age_days(max_age_days)

        async for session in get_session():
            user = await get_or_create_user_by_telegram_id(
                admin_telegram_id, admin_username, session=session
            )
            await session.flush()
            if user.id is None:
                raise RuntimeError("User id is None after get_or_create_user_by_telegram_id")

            existing = await session.execute(
                select(AuthorSettings).where(AuthorSettings.username == username)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Автор @{username} уже добавлен")

            author = AuthorSettings(
                username=username,
                min_likes=min_likes,
                max_post_age_days=max_age_days,
                is_active=True,
                admin_id=user.id,
            )
            session.add(author)
            await session.flush()
            logger.info(
                f"Added author @{username} min_likes={min_likes} max_age_days={max_age_days} admin_id={user.id}"
            )
            return author
        raise RuntimeError("get_session did not yield session")

    @staticmethod
    async def get_author(username: str) -> Optional[AuthorSettings]:
        """Возвращает настройки автора по username или None."""
        username = username.strip().replace("@", "").lower()
        async for session in get_session():
            result = await session.execute(
                select(AuthorSettings).where(AuthorSettings.username == username)
            )
            return result.scalar_one_or_none()
        return None

    @staticmethod
    async def get_all_authors(admin_telegram_id: int) -> List[AuthorSettings]:
        """Возвращает всех авторов, созданных данным админом."""
        user = await get_or_create_user_by_telegram_id(admin_telegram_id)
        async for session in get_session():
            result = await session.execute(
                select(AuthorSettings)
                .where(AuthorSettings.admin_id == user.id)
                .order_by(AuthorSettings.username)
            )
            return list(result.scalars().all())
        return []

    @staticmethod
    async def update_author(
        username: str,
        *,
        min_likes: Optional[int] = None,
        max_age_days: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[AuthorSettings]:
        """
        Обновляет настройки автора.

        Returns:
            Обновлённый AuthorSettings или None, если автор не найден.
        """
        username = username.strip().replace("@", "").lower()
        if min_likes is not None:
            min_likes = _validate_min_likes(min_likes)
        if max_age_days is not None:
            max_age_days = _validate_max_age_days(max_age_days)

        async for session in get_session():
            result = await session.execute(
                select(AuthorSettings).where(AuthorSettings.username == username)
            )
            author = result.scalar_one_or_none()
            if not author:
                return None
            if min_likes is not None:
                author.min_likes = min_likes
            if max_age_days is not None:
                author.max_post_age_days = max_age_days
            if is_active is not None:
                author.is_active = is_active
            await session.flush()
            changes = []
            if min_likes is not None:
                changes.append(f"min_likes={min_likes}")
            if max_age_days is not None:
                changes.append(f"max_age_days={max_age_days}")
            if is_active is not None:
                changes.append(f"is_active={is_active}")
            logger.info(f"Updated author @{username} " + ", ".join(changes))
            return author
        return None

    @staticmethod
    async def remove_author(username: str) -> bool:
        """
        Удаляет автора по username.

        Returns:
            True если удалён, False если не найден.
        """
        username = username.strip().replace("@", "").lower()
        async for session in get_session():
            result = await session.execute(
                select(AuthorSettings).where(AuthorSettings.username == username)
            )
            author = result.scalar_one_or_none()
            if not author:
                return False
            await session.delete(author)
            logger.info(f"Removed author @{username}")
            return True
        return False

    @staticmethod
    async def get_active_authors() -> List[AuthorSettings]:
        """Возвращает только активных авторов (для парсера)."""
        async for session in get_session():
            result = await session.execute(
                select(AuthorSettings)
                .where(AuthorSettings.is_active == True)
                .order_by(AuthorSettings.username)
            )
            return list(result.scalars().all())
        return []
