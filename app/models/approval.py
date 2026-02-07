from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.models.base import Base


class DecisionType(enum.Enum):
    """Типы решений админа."""
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class ApprovalHistory(Base):
    """История одобрений/отклонений постов."""
    
    __tablename__ = "approval_history"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    processed_post_id: Mapped[int] = mapped_column(
        ForeignKey("processed_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Telegram пользователь
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Telegram User ID"
    )
    
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Telegram username"
    )
    
    # Решение
    decision: Mapped[DecisionType] = mapped_column(
        SQLEnum(DecisionType),
        nullable=False,
        index=True
    )
    
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий админа"
    )
    
    # Время
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relations
    processed_post: Mapped["ProcessedPost"] = relationship(
        "ProcessedPost",
        back_populates="approvals"
    )
    
    # ==================== МЕТОДЫ ====================
    
    @classmethod
    async def get_latest_for_post(
        cls,
        session,
        post_id: int
    ) -> Optional["ApprovalHistory"]:
        """Получает последнее решение для поста."""
        from sqlalchemy import select
        result = await session.execute(
            select(cls)
            .where(cls.processed_post_id == post_id)
            .order_by(cls.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    def is_approved(self) -> bool:
        """Проверяет было ли одобрено."""
        return self.decision == DecisionType.APPROVED
    
    def to_dict(self) -> dict:
        """Сериализация в dict."""
        return {
            "id": self.id,
            "processed_post_id": self.processed_post_id,
            "user_id": self.user_id,
            "username": self.username,
            "decision": self.decision.value,
            "comment": self.comment,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"<ApprovalHistory(id={self.id}, post={self.processed_post_id}, decision={self.decision.value})>"
