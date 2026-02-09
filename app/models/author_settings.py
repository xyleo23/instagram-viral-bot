"""
Персональные настройки для каждого автора Instagram.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuthorSettings(Base, TimestampMixin):
    """Настройки парсинга для конкретного автора Instagram."""

    __tablename__ = "author_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Instagram username",
    )
    min_likes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        comment="Минимум лайков для постов этого автора",
    )
    max_post_age_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Максимальный возраст поста в днях",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Участвует ли автор в парсинге",
    )

    admin_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID админа (User), создавшего настройки",
    )

    admin: Mapped["User"] = relationship(
        "User",
        back_populates="author_settings",
    )

    def __repr__(self) -> str:
        return f"<AuthorSettings(username={self.username!r}, min_likes={self.min_likes})>"
