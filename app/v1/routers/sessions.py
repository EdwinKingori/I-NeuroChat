from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import logging

from app.core.db.database import get_db
from app.core.redis.redis_config import get_redis, AsyncRedisClient
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
logger = logging.getLogger("seesion.routes")

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
@router.get("/", response_model=List[SessionResponse])
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
    3. Save to Redis

    """

    logger.info("Listing sessions requested | user_id=%s", user_id)

    cache_key = f"user:{user_id}:sessions"

    # 1️⃣ Redis
    cached = await redis.get(cache_key)
    if cached:
        logger.info(
            "Sessions list served from Redis | user_id=%s count=%d",
            user_id,
            len(cached)
        )
        return cached

    logger.info(
        "Redis session list MISS | Fetching from PostgreSQL | user_id=%s",
        user_id
    )

    # 2️⃣ Retrive from PostgreSQL
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == user_id)
        .order_by(SessionModel.started_at.desc())
    )
    sessions = result.scalars().all()

    response = []
    for session in sessions:
        data = SessionResponse.model_validate(session).model_dump()
        data["source"] = "Postgres DB"
        response.append(data)

    # caching data retrieved from Postgres DB
    await redis.set_json(cache_key, response, ex=3600)

    logger.info(
        "Session list cached in Redis | user_id=%s count=%d",
        user_id,
        len(response)
    )

    return response


# ✅ Route: Updating a user's sessions
@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_in: SessionCreate,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):

    logger.info("Updating session=%s user=%s", session_id, user_id)

    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id, SessionModel.user_id == user_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    for field, value in session_in.model_dump(exclude_unset=True).items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    await cache_session(session, redis)

    logger.info("Session updated id=%s", session_id)
    return SessionResponse.model_validate(session)


# ✅ Route: Deleting a user's session
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Deleting session=%s user=%s", session_id, user_id)

    result = await db.execute(
        select(SessionModel)
        .where(
            SessionModel.id == session_id,
            SessionModel.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    await redis.delete(f"session:{session_id}")
    await redis.delete(f"user:{user_id}:sessions")

    logger.info("Session deleted id+%s", session_id)
