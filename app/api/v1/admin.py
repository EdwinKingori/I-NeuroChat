from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db.database import get_db
from app.core.redis.redis_config import AsyncRedisClient, get_redis
from app.core.logging.route_logger import get_route_logger
from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.require_admin import require_admin
from app.api.dependencies.require_permissions import require_permission

from app.models.users import User
from app.schemas.user import UserResponse, UserRead
from app.services.helpers.crud_helper import CRUDHelper
from app.services.helpers.redis_helpers import fetch_from_cache_or_db
from app.services.helpers.pagination import paginate_query
from app.services.helpers.sorting import apply_sorting

# ✅ Route Logger (standardized)
logger = get_route_logger("admin.routes")


# ✅ Admin Router
router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)

# ✅ Set cache expiry periods
ADMIN_USERS_LIST_TTL = 120
USER_CACHE_TTL = 300


# ✅ LIST USERS (Admin Only)
@router.get(
    "/users", 
    response_model=dict,
    dependencies=[Depends(require_permission("users.read"))],
)
async def list_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    """
    Admin endpoint to retrieve paginated users.
    paginated + sorted integrated with cache-first strategy

    Security:
    - Requires admin privileges (users.read)
    - requires authentication (get_current_user)
    
    Cache Strategy:
    - Redis first (fast)
    - Postgres fallback (source of truth)
    - Cache rehydration on miss
    """

    admin_id = current_user["user_id"]

    logger.info(
        "Admin %s requested users list | page=%s limit=%s sort_by=%s order=%s",
        admin_id, page, limit, sort_by, order
    )

    # ✅ Secure cache key scoped by admin identity
    cache_key = f"admin:{admin_id}:users:list:{page}:{limit}:{sort_by}:{order}"

    async def fetch():
        # 1) Build query
        query = select(User)
        query = apply_sorting(query, User, sort_by, order)

        # 2) Paginate from DB
        users, total = await paginate_query(
            session=db,
            query=query,
            page=page,
            limit=limit,
        )

        # 3) Return JSON-serializable structure for Redis
        return {
            "items": [
                UserResponse.model_validate(u).model_dump(mode="json")
                for u in users
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    # ✅ Cache-first fetch
    data, source = await fetch_from_cache_or_db(
        redis=redis,
        redis_key=cache_key,
        db_fetch_callable=fetch,
        ttl=ADMIN_USERS_LIST_TTL,
    )

    logger.debug(
        "Admin users list served | admin=%s source=%s items=%s",
        admin_id, source, len(data.get("items", []))
    )

    return {**data, "source": source}


# ✅ ACTIVATING USER (Write-through cache)
@router.patch(
    "/users/{user_id}/activate",
    dependencies=[Depends(require_permission("users.activate"))],
)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    """
    Reactivate a user's account.

    Security:
    - Requires authentication
    - Requires RBAC permission: users.activate

    Cache strategy:
    - Postgres is source of truth
    - After DB update, write-through:
        * user:{user_id}
        * admin:user:{user_id} (optional but helps admin reads)
    """

    actor_id = current_user["user_id"]

    logger.warning("Admin %s attempting to activate user %s", actor_id, user_id)

    user = await CRUDHelper.get_by_id(db, User, user_id)
    if not user:
        logger.error("Activate failed | user not found=%s", user_id)
        raise HTTPException(404, "User not found")

    # ✅ DB update (source of truth)
    user = await CRUDHelper.update(db, user, {"is_active": True})

    # ✅ Write-through cache: single-user view
    user_payload = UserRead.model_validate(user).model_dump(mode="json")

    await redis.set_json(
        f"user:{user_id}",
        user_payload,
        ex=USER_CACHE_TTL,
    )

    # ✅ Optional: admin-scoped single-user cache (useful if admin routes read users)
    await redis.set_json(
        f"admin:user:{user_id}",
        user_payload,
        ex=USER_CACHE_TTL,
    )

    logger.info("User activated successfully | user=%s updated_by=%s", user_id, actor_id)

    return {"message": "User activated"}

# ✅ PROMOTE USER TO ADMIN (Write-through cache)
@router.patch(
    "/users/{user_id}/promote",
    dependencies=[Depends(require_permission("users.promote"))],
)
async def promote_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: AsyncRedisClient = Depends(get_redis),
    current_user: dict = Depends(get_current_user),
):
    """
    Assign admin role to a user.

    Security:
    - Requires authentication
    - Requires RBAC permission: users.promote

    Cache strategy:
    - Postgres is source of truth
    - After role assignment, write-through:
        * user:{user_id} (if it includes role info)
        * admin:user:{user_id}
        * user:{user_id}:roles (recommended)
        * user:{user_id}:permissions (recommended)
    """

    actor_id = current_user["user_id"]

    logger.warning("Admin %s attempting to promote user %s", actor_id, user_id)

    user = await CRUDHelper.get_by_id(db, User, user_id)
    if not user:
        logger.error("Promotion failed | user not found=%s", user_id)
        raise HTTPException(404, "User not found")

    # ✅ Role assignment via RBAC mapping
    await CRUDHelper.assign_role(db, user_id, role_name="admin")

    # 🔁 Refresh user (optional but good if schema includes roles/flags)
    user = await CRUDHelper.get_by_id(db, User, user_id)

    # ✅ Write-through cache: single-user view
    user_payload = UserRead.model_validate(user).model_dump(mode="json")

    await redis.set_json(
        f"user:{user_id}",
        user_payload,
        ex=USER_CACHE_TTL,
    )

    await redis.set_json(
        f"admin:user:{user_id}",
        user_payload,
        ex=USER_CACHE_TTL,
    )

    await redis.set_json(
        f"user:{user_id}:roles",
        {"roles": ["admin"]},  # minimal write-through; can be expanded to actual DB fetch
        ex=USER_CACHE_TTL,
    )


    logger.info("User promoted to admin | user=%s updated_by=%s", user_id, actor_id)

    return {"message": "User promoted to admin"}