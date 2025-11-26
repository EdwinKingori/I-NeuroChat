from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Literal
from datetime import datetime

from .user import UserResponse


# ✅ === Base Memory Schema ===
class UserMemoryBase(BaseModel):
    """
    memory_summary:
        LLM-generated behavioral/personality summary.
    """
    memory_summary: str = Field(
        "",
        description="AI generated memory summary for the user"
    )


# ✅ === # Memory Create/Update — mainly for admin or internal tools ===
class UserMemoryUpdate(UserMemoryBase):
    pass


# ✅ Memory Response Schema
class UserMemoryResponse(UserMemoryBase):
    user_id: UUID
    updated_at: datetime

    source: Literal["PostgresDB", "Redis"] = "PostgresDB"

    class Config:
        from_attributes = True


# ✅ Full expanded memory with user info
class UserMemoryRead(UserMemoryResponse):
    """
    Full detailed memory record including user information.
    """
    user: UserResponse
    source: Literal["PostgresDB", "Redis"] = "PostgresDB"

    class Config:
        from_attributes = True
