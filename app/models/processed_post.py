from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin


class ProcessedStatus(enum.Enum):
    """Статусы обработанного поста."""
    PENDING_APPROVAL = "pending_approval"  # Ждет одобрения
    APPROVED = "approved"                  # Одобрен
    REJECTED = "rejected"                  # Отклонен
    POSTED = "posted"                      # Опубликован


class ProcessedPost(Base, TimestampMixin):
    """Обработанный пост (после AI рерайта)."""
    
    __tablename__ = "processed_posts"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    original_post_id: Mapped[int] = mapped_column(
        ForeignKey("original_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # AI обработанный контент
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Новый заголовок"
    )
    
    caption: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Переписанный текст для Instagram"
    )
    
    hashtags: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Хештеги через пробел"
    )
    
    slides: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        comment="Массив текстов для слайдов карусели"
    )
    
    slides_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество слайдов"
    )
    
    # AI метрики
    ai_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Модель AI (например, anthropic/claude-3.5-sonnet)"
    )
    
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Токенов использовано"
    )
    
    cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="Стоимость обработки в USD"
    )
    
    # Изображения
    image_urls: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        comment="URLs сгенерированных изображений"
    )
    
    yandex_disk_folder: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Путь к папке на Яндекс.Диске"
    )
    
    # Статус
    status: Mapped[ProcessedStatus] = mapped_column(
        SQLEnum(ProcessedStatus),
        default=ProcessedStatus.PENDING_APPROVAL,
        nullable=False,
        index=True
    )
    
    # Relations
    original_post: Mapped["OriginalPost"] = relationship(
        "OriginalPost",
        back_populates="processed_posts"
    )
    
    approvals: Mapped[List["ApprovalHistory"]] = relationship(
        "ApprovalHistory",
        back_populates="processed_post",
        cascade="all, delete-orphan"
    )
    
    # ==================== МЕТОДЫ ====================
    
    def get_full_caption(self) -> str:
        """Возвращает полный caption для Instagram."""
        return f"{self.title}\n\n{self.caption}\n\n{self.hashtags}"
    
    def get_telegram_preview(self, max_length: int = 300) -> str:
        """Возвращает короткий превью для Telegram."""
        text = f"📝 {self.title}\n\n{self.caption}"
        if len(text) > max_length:
            text = text[:max_length] + "..."
        return text
    
    def to_dict(self) -> dict:
        """Сериализация в dict."""
        return {
            "id": self.id,
            "original_post_id": self.original_post_id,
            "title": self.title,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "slides": self.slides,
            "slides_count": self.slides_count,
            "ai_model": self.ai_model,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "image_urls": self.image_urls,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"<ProcessedPost(id={self.id}, title='{self.title[:30]}...', status={self.status.value})>"
