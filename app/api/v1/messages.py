from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json
import logging

from app.core.db.database import get_db
from app.core.redis.redis_config import AsyncRedisClient, get_redis
from app.models.message import ChatMessage
from app.schemas.message import (
    ChatMessageCreate, 
    ChatMessageResponse, 
    ChatMessageRead,
)
from app.core.logging.route_logger import get_route_logger
from app.services.helpers.crud_helper import CRUDHelper
from app.services.helpers.redis_helpers import fetch_from_cache_or_db
from app.services.helpers.pagination import paginate_query
from app.services.helpers.sorting import apply_sorting

# ✅ Logger
logger = get_route_logger("messages.routes")

# ✅ Router
router = APIRouter(
    prefix="/api/v1/message",
    tags=["Chat Messages"]
)

# Redis Cache Configuration
MESSAGE_CACHE_TTL = 60 * 5 
SESSION_MESSAGES_TTL = 60 * 2  


# ✅ Create Message Route
@router.post("/", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info(
        "Creating message | user=%s session=%s role=%s source=%s",
        message_data.user_id,
        message_data.session_id,
        message_data.role,
        message_data.source,
    )

    message = await CRUDHelper.create(
        db,
        ChatMessage,
        message_data.model_dump(),
    )

    # Cache single message
    await redis.set_json(
        f"message:{message.id}",
        ChatMessageResponse.model_validate(message).model_dump(mode="json"),
        ex=MESSAGE_CACHE_TTL,
    )

    # Invalidate session message lists
    await redis.delete(f"session:{message.session_id}:messages")

    logger.info("Message created | id=%s", message.id)

    return ChatMessageResponse.model_validate(message)
    

# ✅ FETCHING MESSAGE BY ID
@router.get("/{message_id}", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
async def get_message(
    message_id:UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    async def fetch():
        msg = await CRUDHelper.get_by_id(db, ChatMessage, message_id)
        if not msg:
            return None
        return ChatMessageResponse.model_validate(msg).model_dump()

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=f"message:{message_id}",
        db_fetch_callable=fetch,
        ttl=MESSAGE_CACHE_TTL,
    )

    if not data:
        raise HTTPException(404, "Message not found")

    return ChatMessageResponse(**data, source=source)


# ✅ LIST SESSION MESSAGES
@router.get(
    "/session/{session_id}",
    response_model=dict,
)
async def list_session_messages(
    session_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    """
    Paginated + sorted messages.

    Response:
    {
        items: [...],
        total: int,
        page: int,
        limit: int
    }
    """

    cache_key = f"session:{session_id}:messages:{page}:{limit}:{sort_by}:{order}"

    async def fetch():
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        )

        # Apply safe sorting
        query = apply_sorting(query, ChatMessage, sort_by, order)

        messages, total = await paginate_query(
            session=db,
            query=query,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                ChatMessageResponse.model_validate(m).model_dump()
                for m in messages
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=cache_key,
        db_fetch_callable=fetch,
        ttl=SESSION_MESSAGES_TTL,
    )

    return {
        **data,
        "source": source
    }


# ==================================================
# ✅ DELETE MESSAGE
# ==================================================
@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    message = await CRUDHelper.get_by_id(db, ChatMessage, message_id)

    if not message:
        raise HTTPException(404, "Message not found")

    await CRUDHelper.delete(db, message)

    # Cache invalidation
    await redis.delete(f"message:{message_id}")
    await redis.delete(f"session:{message.session_id}:messages")

    logger.info("Message deleted | id=%s", message_id)
