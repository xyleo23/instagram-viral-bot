from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime


# Declarative Base
class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# Mixin для timestamp полей
class TimestampMixin:
    """Добавляет created_at и updated_at ко всем моделям."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# Database engine (глобальный)
engine = None
async_session_maker = None


def init_db(database_url: str) -> None:
    """
    Инициализирует подключение к БД.
    
    Args:
        database_url: PostgreSQL connection string (asyncpg)
    """
    global engine, async_session_maker
    
    engine = create_async_engine(
        database_url,
        echo=False,  # Установи True для debug SQL запросов
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Проверка соединения
        pool_recycle=3600,   # Переподключение каждый час
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


async def create_tables() -> None:
    """Создает все таблицы в БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Удаляет все таблицы из БД (осторожно!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_session():
    """
    Async context manager для сессии БД.

    Usage:
        async with get_session() as session:
            result = await session.execute(select(User))
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Для совместимости
@asynccontextmanager
async def get_db():
    """Алиас для get_session()."""
    async with get_session() as session:
        yield session
