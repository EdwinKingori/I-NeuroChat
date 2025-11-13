import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserMemory(Base):
    __tablename__ = "user_memory"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    # LLM-generated summary e.g., - "User JOhn Doe is a data engineer learning Spanish. Prefers concise answers with code examples."
    memory_summary = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())

    # Back_reference relationship
    user = relationship("User", back_populates="memory", uselist=False)
