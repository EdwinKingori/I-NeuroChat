from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.redis_config import get_redis, AsyncRedisClient
from app.models.session import ConversationSession as SessionModel
from app.schemas.session import SessionCreate, SessionRead, SessionResponse
from app.services.redis.redis_session_helpers import (
    cache_session,
    get_cached_session,
    fetch_session_and_cache,
)

router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)
logger = logging.getLogger(__name__)

# == ✅ Redis TTL for Caching ==
SESSION_TTL = 24 * 3600


# ✅ === CREATE SESSION ===
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_Session(
    session_in: SessionCreate,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Create a ConversationSession assigned to `user_id`.
    """
    logger.info("Creating session for user %s", user_id)

    session = SessionModel(
        user_id=user_id,
        title=session_in.title,
        language=session_in.language or "en",
        model_used=session_in.model_used or "gpt-5",
        platform=session_in.platform or "web",
        system_prompt=session_in.system_prompt,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    response = SessionResponse.model_validate(session)
    response_dict = response.model_dump()
    response_dict["source"] = "Postgres DB"

    await cache_session(session, redis)

    return response_dict


# ✅ Route: Fetch session by ID(cache-first)
@router.get("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_session(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Fetch session by ID:
    Logical Flow:
    1. Attempt Redis cache
    2. If cache miss -> fetch from PostgreSQL
    3. Cache the DB result in Redis
    """

    logger.info("READ session requested | session_id= %s user_id=%s",
                session_id, user_id)

    # 1️⃣ Attempt to fetch from Redis first
    cached = await get_cached_session(session_id, redis)

    # authorization verification
    if cached:
        if cached.get("user_id") != str(user_id):
            logger.warning(
                "Unauthorized Redis cache access | session_id=%s user_id=%s",
                session_id,
                user_id
            )
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(
            "Session served from Redis | session_id=%s",
            session_id
        )

        return cached

    # 2️⃣ PostgreSQL fallback
    result = await db.execute(
        select(SessionModel)
        .where(
            SessionModel.id == session_id,
            SessionModel.user_id == user_id
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        logger.warning(
            "Session not found in DB |  session_id=%s user_id=%s",
            session_id,
            user_id
        )
        raise HTTPException(status_code=404, detail="Session not found")

    # 3️⃣ Serialize + cache
    response = SessionResponse.model_validate(session).model_dump()
    response["source"] = "Postgres DB"

    await redis.set_json(f"session:{session_id}", response, ex=SESSION_TTL)

    logger.info(
        "Session fetched from PostgreSQL and cached | session_id=%s",
        session_id
    )

    return response


# ✅ Route: Fetching all user's sessions
@router.get("/sessions", response_model=List[SessionResponse])
async def list_user_sessions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
     List all sessions owned by a user.
     Logical flow:
    1. Attempt Redis list cache.
    2. Fallback to PostgrSQL

    """

    logger.info("Listing sessions requested | user_id=%s", user_id)

    cache_key = f"user:{user_id}:sessions"
