from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db.database import get_db
from app.core.logging.route_logger import get_route_logger
from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.require_admin import require_admin
from app.api.dependencies.require_permissions import require_permission

from app.models.users import User
from app.schemas.user import UserResponse
from app.services.helpers.crud_helper import CRUDHelper
from app.services.helpers.pagination import paginate_query


# ✅ Route Logger (standardized)
logger = get_route_logger("admin.routes")


# ✅ Admin Router
router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)


# ✅ LIST USERS (Admin Only)
@router.get(
    "/users", 
    response_model=dict,
    dependencies=[Depends(require_permission("users.read"))],
)
async def list_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Admin endpoint to retrieve paginated users.

    Security:
    - Requires admin privileges
    """

    logger.info(
        "Admin %s requested users list | page=%s limit=%s",
        current_user["user_id"],
        page,
        limit,
    )

    users, total = await paginate_query(
        session=db,
        query=select(User),
        page=page,
        limit=limit,
    )

    logger.debug("Users fetched | count=%s", len(users))

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "limit": limit,
    }

# ✅ ACTIVATING USER
@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Reactivate a user's account.

    Rules:
    - Requires "users.activity" permission
    """

    logger.warning(
        "User %s attempting to activate user %s",
        current_user["user_id"],
        user_id,
    )

    user = await CRUDHelper.get_by_id(db, User, user_id)

    if not user:
        logger.error("Activate failed | user not found=%s", user_id)
        raise HTTPException(404, "User not found")

    await CRUDHelper.update(db, user, {"is_active": True})

    logger.info("User activated successfully | user=%s", user_id)

    return {"message": "User activated"}


# ✅ PROMOTE USER TO ADMIN

@router.patch(
    "/users/{user_id}/promote",
    dependencies=[Depends(require_permission("users.promote"))],
)
async def promote_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
   Assign ADMIN or support role to a user.

    Rules:
    - Permissions needed: requires "users.promote" permission
    """

    logger.warning(
        "User %s attempting to promote user %s",
        current_user["user_id"],
        user_id,
    )

    user = await CRUDHelper.get_by_id(db, User, user_id)

    if not user:
        logger.error("Promotion failed | user not found=%s", user_id)
        raise HTTPException(404, "User not found")

    # ✅ Role assignment handled via RBAC (NOT boolean flag)
    await CRUDHelper.assign_role(db, user_id, role_name="admin")

    logger.info("User promoted to admin | user=%s", user_id)

    return {"message": "User promoted to admin"}
