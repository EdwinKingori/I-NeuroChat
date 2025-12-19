from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import list
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


# ✅ Route: GET session by ID(cache-first)
@router.get("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Fetch session by ID
    """
    # 1️⃣ Attempt to fetch from Redis first
    cached = await get_cached_session(session_id, redis)
    if cached:
        return cached

    # 2️⃣ Fallback to DB
    return await fetch_session_and_cache(session_id, db, redis)
