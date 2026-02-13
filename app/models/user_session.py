import secrets
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db.database import Base

class UserSession(Base):
    """
    Represents authenticated user sessions.

    Design:
    - PostgreSQL → Source of truth
    - Redis → Fast validation cache
    - session_key → Opaque token (NOT JWT)
    """

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_key = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: secrets.token_urlsafe(48),
    )

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="auth_sessions")
