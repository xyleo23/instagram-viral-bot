"""
Модель пользователя (админ бота) для связи с настройками авторов.
"""
from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.author_settings import AuthorSettings


class User(Base, TimestampMixin):
    """Пользователь бота (админ). Идентифицируется по Telegram ID."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram User ID",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Telegram username",
    )

    author_settings: Mapped[List["AuthorSettings"]] = relationship(
        "AuthorSettings",
        back_populates="admin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"
