import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    user_id: str,
    email: str,
    roles: list[str],
    session_key: str,
) -> str:
    """
    Short-lived access token (default 15 min).
    Contains: user identity, roles, and session reference (sid).
    """
    settings = get_settings()
    now = _utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "sid": session_key,   # links token to a specific DB session (enables revocation)
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, session_key: str) -> str:
    """
    Long-lived refresh token. jti = session_key for DB lookup on refresh/logout.
    """
    settings = get_settings()
    now = _utcnow()
    payload = {
        "sub": user_id,
        "jti": session_key,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises jwt.PyJWTError subclasses on failure:
    - jwt.ExpiredSignatureError  → token has expired
    - jwt.InvalidTokenError      → bad signature or malformed
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
