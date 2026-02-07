from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
import enum

from app.models.base import Base, TimestampMixin


class PostStatus(enum.Enum):
    """Статусы оригинального поста."""
    PARSING = "parsing"          # Только что распарсен
    FILTERED = "filtered"        # Прошел фильтр (вирусный)
    PROCESSING = "processing"    # В обработке AI
    PROCESSED = "processed"      # Обработан AI
    APPROVED = "approved"        # Одобрен админом
    REJECTED = "rejected"        # Отклонен админом
    POSTED = "posted"           # Опубликован в Instagram


class OriginalPost(Base, TimestampMixin):
    """Оригинальный пост из Instagram."""
    
    __tablename__ = "original_posts"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Instagram данные
    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Instagram post ID"
    )
    
    author: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Instagram username"
    )
    
    author_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="URL профиля автора"
    )
    
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Полный текст поста"
    )
    
    # Метрики
    likes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Количество лайков"
    )
    
    comments: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Количество комментариев"
    )
    
    engagement: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Коэффициент вовлеченности (likes/followers)"
    )
    
    # URLs
    post_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Прямая ссылка на пост"
    )
    
    # Даты
    posted_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Когда пост был создан в Instagram"
    )
    
    # Статус
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus),
        default=PostStatus.PARSING,
        nullable=False,
        index=True
    )
    
    # Relations
    processed_posts: Mapped[List["ProcessedPost"]] = relationship(
        "ProcessedPost",
        back_populates="original_post",
        cascade="all, delete-orphan"
    )
    
    # ==================== МЕТОДЫ ====================
    
    def is_viral(self, min_likes: int = 5000) -> bool:
        """Проверяет является ли пост вирусным."""
        return self.likes >= min_likes
    
    def days_old(self) -> int:
        """Возвращает возраст поста в днях."""
        return (datetime.utcnow() - self.posted_at).days
    
    def is_fresh(self, max_days: int = 3) -> bool:
        """Проверяет является ли пост свежим."""
        return self.days_old() <= max_days
    
    def to_dict(self) -> dict:
        """Сериализация в dict."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "author": self.author,
            "text": self.text,
            "likes": self.likes,
            "comments": self.comments,
            "engagement": self.engagement,
            "post_url": self.post_url,
            "posted_at": self.posted_at.isoformat(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"<OriginalPost(id={self.id}, author=@{self.author}, likes={self.likes}, status={self.status.value})>"


# Индексы для быстрого поиска
Index("idx_author_likes", OriginalPost.author, OriginalPost.likes.desc())
Index("idx_status_created", OriginalPost.status, OriginalPost.created_at.desc())
