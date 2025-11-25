from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .user import UserResponse
from .session import SessionResponse


# ✅ === Base ChatMessage Schema ===
class ChatMessageBase(BaseModel):
    role: str = Field(
        ...,
        max_length=20,
        description="Message role: 'user', 'assistant', or 'system'."
    )
    content: str = Field(
        ...,
        description="Text content of the message. If the message is audio, this contains transcript text."
    )
    source: str = Field(
        "text",
        max_length=32,
        description="Source of message: 'text' or 'audio'."
    )
    # MVP audio: store base64-encoded audio
    audio_data: Optional[str] = Field(
        None,
        description="Base64-encoded audio data (temporary MVP storage)."
    )


# ✅ === Schema for Creating a ChatMessage ===
class ChatMessageCreate(ChatMessageBase):
    """
    Incoming message schema for API/WebSocket.

    session_id:
        The session this message belongs to.
        Provided by client in HTTP workflow,
        OR derived automatically in WebSocket session.
    """
    user_id: UUID
    session_id: UUID


# ✅ ===Lightweight ChatResponse Schema (embedded inside SessionRead)
class ChatMessageResponse(ChatMessageBase):
    """
    Lightweight serializer for returning messages.
    Session/user objects not included to avoid circular references.
    """
    id: UUID
    user_id: UUID
    session_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ✅ === Expanded chat message including user + session
# Get /message{id}
class ChatMessageRead(ChatMessageResponse):
    """
    Full message representation including:
    - User data -> UserResponse
    - Session summary -> SessionResponse

    Useful for detailed message inspection or admin debugging tools.
    """
    user: UserResponse
    session: SessionResponse

    class Config:
        from_attriibutes = True
