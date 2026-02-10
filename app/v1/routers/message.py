from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from app.core.database import get_db
from app.core.redis_config import AsyncRedisClient, get_redis
from app.models.message import ChatMessage
from app.schemas.message import ChatMessageCreate, ChatMessageRead

# ✅ Logger
logger = logging.getLogger("messages.routes")

# ✅ Router
router = APIRouter(
    prefix="/api/v1/message",
    tags=["Chat Messages"]
)


# ✅ Create Route
