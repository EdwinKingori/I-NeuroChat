from pydantic import BaseModel, EmailStr, model_validator
from uuid import UUID
from typing import Optional

# ✅ Login Request 
class LoginRequest(BaseModel):
    email:Optional[EmailStr] = None
    username: Optional[str] = None
    password: str
    remember_me: Optional[bool] = False

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.email and not self.username:
            raise ValueError("Eaither email or username must be provided")
        return self

# ✅ Session Response
class SessionTokenResponse(BaseModel):
    session_key:str
    user_id: UUID
    source:str

# ✅ LogOut Response
class LogoutResponse(BaseModel):
    message: str
