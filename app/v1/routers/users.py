from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import json
import logging

from app.core.logging_config import setup_logging
from app.core.database import get_db
from app.core.redis_config import AsyncRedisClient, get_redis
from app.models.users import User
from app.schemas.user import UserCreate, UserResponse, UserRead, UserUpdate

# ✅ Logging setup
setup_logging()
logger = logging.getLogger("users.routes")

# ✅ Router
router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

# Redis TTL for caching
USER_CACHE_TTL = 300  # -> 5 minutes


# ✅ === CREATE USER ===
@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Creating a new User.
    - Storing user data in PostgreSQL
    - Cache data in Redis for quick access
    """

    # Verify is user data exists
    user_exists = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    result = await db.execute(user_exists)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=f"temp_hash_{user_data.password}"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Cache the user's data in Redis
    cache_key = f"user:{new_user.id}"
    user_dict = {
        "id": str(new_user.id),
        "username": new_user.username,
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "created_at": new_user.created_at.isoformat(),
        "updated_at": new_user.updated_at.isoformat() if new_user.updated_at else None
    }
    await redis.set_json(cache_key, user_dict, ex=USER_CACHE_TTL)

    logger.info(f"User created: {user_data.username} (ID: {new_user.id})",)

    return UserRead(
        **user_dict,
        source="PostgresDB"
    )


# ✅ === FETCH USER BY ID ===
@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Retrieve user by ID:
    - first check Redis cache
    - falls back to PostgreSQL if not cached
    """
    cache_key = f"user:{user_id}"

    # Attempt retrieving from Redis first
    cached_user = await redis.get_json(cache_key)
    if cached_user:
        logger.info(f"User {user_id} retrieved from Redis")
        return UserRead(
            **cached_user,
            source="Redis"
        )

    # fetch from POstgreSQL
    user = select(User).where(User.id == user_id)
    result = await db.execute(user)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Cache for future requests
    user_dict = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

    await redis.set_json(cache_key, user_dict, ex=USER_CACHE_TTL)

    logger.info(f"📊 User {user_id} retrieved from PostgreSQL")
    return UserRead(
        **user_dict,
        source="PostgresDB"
    )


# ✅ === Fetch ALL USERS ===
@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Listing all users with pagination
    """
    all_users = select(User).offset(skip).limit(limit)
    result = await db.execute(all_users)
    users = result.scalars().all()

    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            source="PostgresDB"
        )
        for user in users
    ]


# ✅ === UPDATE USER ===
@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis)
):
    """
    Updating user details.
    - The configuration updates PostgreSQL
    - And invalidates Redis cache
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(user, "hashed_password", f"temp_hash_{value}")
        else:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    # Invalidate cache
    cache_key = f"user:{user_id}"
    await redis.delete(cache_key)

    logger.info(f"✏️ User {user_id} updated")

    user_dict = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

    return UserRead(**user_dict, source="PostgresDB")


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
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    await db.delete(user)
    await db.commit()

    # Invalidate cache
    cache_key = f"user:{user_id}"
    await redis.delete(cache_key)

    logger.info(f"🗑️ User {user_id} deleted")
