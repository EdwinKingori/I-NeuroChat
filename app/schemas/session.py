from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List

from .user import UserResponse
from .message import ChatMessageResponse


# ✅ === Base Session Schema ===
class SessionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, max_length=50)
    model_used: Optional[str] = Field("gpt-5", max_length=100)
    platform: Optional[str] = Field("web", max_length=50)
    system_prompt: Optional[str] = Field(
        None,
        max_length=512,
        description="Optional system prompt injected at session start."
    )


# ✅ === Schema for creating a session ===
class SessionCreate(SessionBase):
    """
    user_id will NOT be exposed since it is derived from the authenticated user.
    """
    pass


# ✅ Lightweight Session response schema (serializer)
class SessionResponse(SessionBase):
    id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: int
    source: Optional[str] = Field(
        ...,
        description="Source of the data: 'redis' or 'postgres'"
    )

    class Config:
        from_attributes = True


# ✅ === Session schema with user and messages ===
class SessionRead(SessionResponse):
    """
    Expanded session Response. Includes:
    - User who owns the session
    - All the messages in the session
    """
    user: UserResponse
    message: List[ChatMessageResponse] = []

    source: Optional[str] = Field(
        ...,
        description="Source of the data: 'redis' or 'postgres'"
    )

    class Config:
        from_attributes = True
