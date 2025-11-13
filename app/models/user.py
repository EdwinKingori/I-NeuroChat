import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=True)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Relationships
memory = relationship(
    "UserMemory",
    back_populates="user",
    uselist=False,
    cascade="all, delete-orphan",
    passive_deletes=True
)

sessions = relationship(
    "UserMemory",
    back_populate="user",
    uselist=False,
    cascade="all, delete-orphan",
    passive_deletes=True
)

messages = relationship(
    "ChatMessage",
    back_populates="user",
    cascade="all, delete-orphan",
    passive_deletes=True
)
