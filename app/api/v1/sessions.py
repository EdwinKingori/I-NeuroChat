from fastapi import Depends, APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.db.database import get_db
from app.core.redis.redis_config import get_redis, AsyncRedisClient
from app.models.session import ConversationSession as SessionModel
from app.schemas.session import (
    SessionCreate, 
    SessionResponse, 
    SessionUpdate,
)
from app.core.logging.route_logger import get_route_logger
from app.services.helpers.crud_helper import CRUDHelper
from app.services.helpers.redis_helpers import fetch_from_cache_or_db
from app.services.helpers.pagination import paginate_query
from app.services.helpers.sorting import apply_sorting



# == ✅ Logging
logger =get_route_logger("sessions.routes")


# == ✅ Router
router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)

# == ✅ Redis TTL for Caching ==
SESSION_TTL = 24 * 3600
SESSION_LIST_TTL = 300


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

    session = await CRUDHelper.create(
        db,
        SessionModel,
        {**session_in.model_dump(), "user_id": user_id},
    )
    
    session_data = SessionResponse.model_validate(session).model_dump()

    # Write-Through Redis
    await redis.set_json(
        f"session:{session.id}",
        session_data,
        ex=SESSION_TTL,
    )

    logger.info("Session created + cached | id=%s", session.id)

    return SessionResponse(
        **session_data,
         source="PostgreSQL DB",
    )


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

    async def fetch():
        session = await CRUDHelper.get_by_id(db, SessionModel, session_id)

        if not session or session.user_id != user_id:
            return None

        return SessionResponse.model_validate(session).model_dump()

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=f"session:{session_id}",
        db_fetch_callable=fetch,
        ttl=SESSION_TTL,
    )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found"
        )

    return SessionResponse(**data, source=source)


# ✅ Route: Fetching all user's sessions (Pagination and Sorting Integrated)
@router.get("/", response_model=List[SessionResponse])
async def list_user_sessions(
    user_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    sort_by: str = Query("started_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    """
    List all sessions owned by a user.
    Logical flow:
    1. Attempt Redis list cache.
    2. Fallback to PostgrSQL
    3. Save to Redis

    """

    cache_key = f"user:{user_id}:sessions:{page}:{limit}:{sort_by}:{order}"

    async def fetch():
        query = select(SessionModel).where(
            SessionModel.user_id == user_id
        )

        query = apply_sorting(query, SessionModel, sort_by, order)

        sessions, total = await paginate_query(
            session=db,
            query=query,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                SessionResponse.model_validate(s).model_dump(mode="json")
                for s in sessions
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=cache_key,
        db_fetch_callable=fetch,
        ttl=SESSION_LIST_TTL,
    )

    return {**data, "source": source}


# ✅ Route: Updating a user's sessions
@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_update: SessionUpdate,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):

    logger.info("Updating session=%s user=%s", session_id, user_id)

    session = await CRUDHelper.get_by_id(db, SessionModel, session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(404, "Session not found")

    update_data = session_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(400, "No valid fields provided for update")

    session = await CRUDHelper.update(db, session, update_data)

    session_schema = SessionResponse.model_validate(session)
    session_dict = session_schema.model_dump()

    # ✅ WRITE-THROUGH CACHE UPDATE
    await redis.set_json(
        f"session:{session_id}",
        session_dict,
        ex=SESSION_TTL,
    )

    logger.info("Session metadata updated & cache refreshed | id=%s", session_id)

    return session_schema


# ✅ Route: Deleting a user's session
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Deleting session=%s user=%s", session_id, user_id)

    session = await CRUDHelper.get_by_id(db, SessionModel, session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(404, "Session not found")

    await CRUDHelper.delete(db, session)

    await redis.delete(f"session:{session_id}")
    await redis.delete(f"user:{user_id}:sessions")

    logger.info("Session deleted | id=%s", session_id)