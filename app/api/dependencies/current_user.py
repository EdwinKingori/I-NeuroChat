from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.db.database import get_db
from app.models.users import User
from app.core.logging.route_logger import get_route_logger
from app.core.redis.redis_config import get_redis, AsyncRedisClient
from app.models.user_session import UserSession


# ✅ Logging
logger = get_route_logger("auth.dependencies")

# ✅ User Session's-Auth dependency 
async def get_current_user(
    session_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    """
    Resolve authenticated user from session_key.

    Flow:
    1️⃣ Redis Session validation
    2️⃣ PostgreSQL fallback
    3️⃣ Load User
    """

    if not session_key:
        raise HTTPException(401, "Authentication required")

    cached = await redis.get_json(f"session:{session_key}")

    user_id: str | None = None

    if cached:
        if not cached.get("is_active"):
            raise HTTPException(401, "Session expired")
        user_id = cached.get("user_id")
    else:
        # PostgreSQL fallback if cache miss or interrupted
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_key == session_key,
                UserSession.is_active == True,
            )
        )

        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(401, "Invalid or expired session")
    
        user_id = str(session.user_id)

        # Rehydrate Redis by Write-Through Process
        await redis.set_json(
            f"session:{session_key}",
            {
                "user_id": user_id,
                "is_active": True,
            },
            ex=86400,
        )

    # Loading User
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(401, "User no longer exists")
    
    # ✅ Blocking Inactive Users
    if not user.is_active:
        raise HTTPException(403, "Account deactivated")

    logger.debug(
        "Authenticated user=%s admin=%s",
        user.id,
    )

    return {
        "user_id": str(user.id),
        "is_active": user.is_active,
    }
