from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import or_

from app.core.db.database import get_db
from app.core.logging.route_logger import get_route_logger
from app.core.redis.redis_config import get_redis, AsyncRedisClient
from app.models.users import User
from app.models.user_session import UserSession
from app.schemas.auth import (
    LoginRequest,
    SessionTokenResponse,
    LogoutResponse,
)
from app.services.helpers.crud_helper import CRUDHelper


# ✅ Logging
logger = get_route_logger("auth.routes")

# ✅ Router
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

SESSION_TTL = 86400          # 1 day
REMEMBER_TTL = 2592000       # 30 days


# ✅ LOGIN Router
@router.post("/login", response_model=SessionTokenResponse)
async def login(
    payload:LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Login attempt | email=%s", payload.email)

    # Conditions for logging in - Check whether the username or email provided matches. 
    conditions = []
    if payload.email:
        conditions.append(User.email == payload.email)
    if payload.username:
        conditions.append(User.username == payload.username)

    result = await db.execute(
        select(User).where(or_(*conditions))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
        )

    # ⚠️ To Replace with real password verification later
    if user.hashed_password != f"temp_hash_{payload.password}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )

    # When sucessful save session
    session = await CRUDHelper.create(
        db,
        UserSession,
        {"user_id": user.id},
    )

    ttl = REMEMBER_TTL if payload.remember_me else SESSION_TTL

    await redis.set_json(
        f"session:{session.session_key}",
        {
            "user_id": str(user.id),
            "is_active": True,
        },
        ex=ttl,
    )

    logger.info("Login success | user=%s remember=%s", user.id, payload.remember_me)

    return SessionTokenResponse(
        session_key=session.session_key,
        user_id=user.id,
        source="PostgreSQL DB",
    )


# ✅ LOGOUT
@router.post("/logout", response_model=LogoutResponse)
async def logout(
    session_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Logout attempt | session=%s", session_key)

    result = await db.execute(
        select(UserSession).where(
            UserSession.session_key == session_key,
            UserSession.is_active == True,
        )
    )

    session = result.scalar_one_or_none()
    # Validate session
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
             detail= "Invalid session"
        )

    # Update session in DB
    session = await CRUDHelper.update(
        db,
        session,
        {"is_active": False},
    )

    # Invalidate session
    await redis.delete(f"session:{session_key}")

    logger.info("Logout success | session=%s", session_key)

    return LogoutResponse(
        message="Logged out successfully"
    )
