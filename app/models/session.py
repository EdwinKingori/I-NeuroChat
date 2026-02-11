import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db.database import Base


# ✅ === SESSIONS TABLE ===
class ConversationSession(Base):
    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4, index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Explicit metadata columns (Instead of having a JSON column)
    title = Column(String(255), nullable=True)
    language = Column(String(50), default="en")
    model_used = Column(String(100), default="gpt-5")  # LLM version
    platform = Column(String(50), default="web")  # web or mobile
    system_prompt = Column(String(512), nullable=True)  # optional context

    started_at = Column(DateTime(timezone=True),
                        server_default=func.now(), index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="sessions")

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
