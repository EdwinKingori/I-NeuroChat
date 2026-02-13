from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db.database import get_db
from app.api.dependencies.current_user import get_current_user
from app.models.users import User


def require_permission(permission_name: str):
    async def checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        user_id = current_user["user_id"]

        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()

        permissions = {
            perm.name
            for role in user.roles
            for perm in role.permissions
        }

        if permission_name not in permissions:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

        return current_user

    return checker
