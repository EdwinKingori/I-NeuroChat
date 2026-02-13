from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
user_email_ctx: ContextVar[Optional[str]] = ContextVar("user_email", default=None)
user_role_ctx: ContextVar[Optional[str]] = ContextVar("user_role", default=None)

def set_request_context(
    *, 
    request_id:str,
    user_id:str | None = None,
    user_email:str | None =None,
    user_role:str | None =None,
):
    request_id_ctx.set(request_id)
    user_id_ctx.set(user_id)
    user_email_ctx.set(user_email)
    user_role_ctx.set(user_role)

def get_logging_context()-> dict:
    return {
        "request_id": request_id_ctx.get(),
        "user_id": user_id_ctx(),
        "user_email": user_email_ctx.get(),
        "user_role": user_role_ctx.get(),
    }