from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional


# ✅ == User's Base ===
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str
    last_name: str


# ✅ === Creating a User ===
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def validate_password(cls, v):
        """
        Ensuring the password is secure:
        - Minimum length: 8 characters
        - At least one uppercase letter
        - At least one number
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in v):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not any(c.isdigit()for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ✅ === Updating User's Details ===
class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(None, description="Updated email")
    first_name: Optional[str] = Field(None, description="Updated first name")
    last_name: Optional[str] = Field(None, description="Updated second name")
    password: Optional[str] = Field(
        None, min_length=8, description="Updated password")


# ✅ === Lightweight representation of user's schema: Safe for embedding inside other schemas ===
class UserResponse(UserBase):
    """
    To be used when referencing this user's inside other schemas
    It will only contain non-sensitive public fields
    """
    id: UUID
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    source: Optional[str] = None

    class Config:
        from_attributes = True


# ✅ === Public User schema ===
class UserRead(UserResponse):
    """
    Full user representation used for returning user details.
    To be used in API responses where a complete user view is required
    """
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
