from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import json
import logging

from app.api.dependencies.current_user import get_current_user
from app.core.logging.logging_config import setup_logging
from app.core.db.database import get_db
from app.core.redis.redis_config import AsyncRedisClient, get_redis
from app.models.users import User
from app.schemas.user import UserCreate, UserResponse, UserRead, UserUpdate
from app.core.logging.route_logger import get_route_logger

from app.services.helpers.crud_helper import CRUDHelper
from app.services.helpers.redis_helpers import fetch_from_cache_or_db
from app.services.helpers.pagination import paginate_query
from app.services.helpers.sorting import apply_sorting


# ✅ Logging setup
logger = get_route_logger("users.routes")

# ✅ Router
router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

# Redis TTL for caching
USER_CACHE_TTL = 300  # -> 5 minutes
USERS_LIST_TTL = 120 


# ✅ === CREATE USER ===
@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Creating user | username=%s", payload.username)

    # Check duplicates
    existing = await CRUDHelper.get_all(
        db,
        User,
        filters=[
            (User.username == payload.username) |
            (User.email == payload.email)
        ],
        limit=1
    )

    if existing:
        raise HTTPException(400, "Username or email already registered")

    user = await CRUDHelper.create(
        db,
        User,
        {
            **payload.model_dump(exclude={"password"}),
            "hashed_password": f"temp_hash_{payload.password}",
        }
    )

    user_data = UserRead.model_validate(user).model_dump()

    # Write-through Redis Cache
    await redis.set_json(
        f"user:{user.id}",
        user_data,
        ex=USER_CACHE_TTL,
    )

    logger.info("User created + cached success!| id=%s", user.id)

    return UserRead(
        **user_data,
        source="PostgreSQL DB",
    )



# ✅ === FETCH USER BY ID ===
@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve user by ID:
    - first check Redis cache
    - falls back to PostgreSQL if not cached
    """
    requester_id = current_user["user_id"]

    # ✅ Ownership check (basic model)
    if str(user_id) != requester_id:
        raise HTTPException(403, "Not authorized to view this user")
    
    async def fetch():
        user = await CRUDHelper.get_by_id(db, User, user_id)
        if not user:
            return None
        return UserRead.model_validate(user).model_dump(mode="json")

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=f"user:{requester_id}:{user_id}",
        db_fetch_callable=fetch,
        ttl=USER_CACHE_TTL,
    )

    if not data:
        raise HTTPException(404, "User not found")

    return UserRead(**data, source=source)


# ✅ Fetching all USERS (Pagination and Sorting Integrated)
@router.get("/", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    cache_key = f"users:list:{page}:{limit}:{sort_by}:{order}"

    async def fetch():
        query = select(User)

        query = apply_sorting(query, User, sort_by, order)

        users, total = await paginate_query(
            session=db,
            query=query,
            page=page,
            limit=limit,
        )

        return {
            "items": [
                UserResponse.model_validate(u).model_dump(mode="json")
                for u in users
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=cache_key,
        db_fetch_callable=fetch,
        ttl=USERS_LIST_TTL,
    )

    return {**data, "source": source}



# ✅ === UPDATE USER ===
@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
):
    logger.info("Updating user | id=%s", user_id)

    user = await CRUDHelper.get_by_id(db, User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = f"temp_hash_{update_data.pop('password')}"

    user = await CRUDHelper.update(db, user, update_data)

    user_data = UserRead.model_validate(user).model_dump()

    # ✅ WRITE-THROUGH: update cache instead of deleting
    await redis.set_json(
        f"user:{user_id}",
        user_data,
        ex=USER_CACHE_TTL,
    )

    logger.info("User updated + cache refreshed | id=%s", user_id)

    return UserRead(
        **user_data, 
        source="PostgreSQL DB",
    )


# ✅ === DELETE USER ===
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Deleting a user.
    - Removing user data from PostgreSQL (cascades to sessions, messages, memory)
    - Invalidates Redis cache
    """

    logger.info("Delete requested for user %s", user_id)
    
    user = CRUDHelper.get_by_id(db, User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    await CRUDHelper.delete(db, user)

    # Invalidate cache
    await redis.delete(f"user:{user_id}")
    await redis.delete("users:list")

    logger.info(f"🗑️ User {user_id} deleted! ")
