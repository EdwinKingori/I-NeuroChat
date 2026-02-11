import logging
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.redis.redis_config import AsyncRedisClient
from app.models.session import ConversationSession as SessionModel
from app.schemas.session import SessionResponse


logger = logging.getLogger(__name__)

# == ✅ Redis TTL for Caching ==
SESSION_TTL = 24 * 3600


# ======================
# ✅ REDIS CONFIG HELPERS
# ======================


# Cache Session
async def cache_session(
    session: SessionModel,
    redis: AsyncRedisClient
):
    data = SessionResponse.model_validate(session).model_dump()
    data["source"] = "Redis Cache"

    await redis.set_json(
        f"session:{session.id}", data, ex=86400 * 7
    )  # 7 days

    # also cache user sessions list key
    await redis.set_json(
        f"user:{session.user_id}:sessions",
        [{**data, "session_id": str(session.id)}],
        ex=3600
    )
    logger.debug("Session %s cached in Redis", session.id)


# Read session from cache
async def get_cached_session(
    session_id: UUID,
    redis: AsyncRedisClient
) -> dict | None:
    """
    Attempting to read a session from Redis.
    """
    cached = await redis.get_json(f"session:{session_id}")
    if cached:
        cached["source"] = "Redis Cache"
        logger.debug("Session %s served from Redis", session_id)
    return cached


# Fetch Session from DB & Cache it Helper
async def fetch_session_and_cache(
    session_id: UUID,
    db: AsyncSession,
    redis: AsyncRedisClient
) -> dict:

    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    data = SessionResponse.model_validate(session).model_dump()
    data["source"] = "Postgre DB"

    await redis.set_json(
        f"session:{session_id}",
        data,
        ex=SESSION_TTL
    )

    return data
