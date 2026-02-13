from typing import Type, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.roles import Role
from app.models.user_roles import UserRole


class CRUDHelper:
    """
    Generic async CRUD helper.

    Rules:
    - DB access only
    - No business logic
    - Safe commit + rollback
    """

    # 1️⃣ Fetch by ID
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        model: Type,
        obj_id: UUID,
    ):
        result = await db.execute(
            select(model).where(model.id == obj_id)
        )
        return result.scalar_one_or_none()

    # 2️⃣ Fetch all with filters / pagination / ordering
    @staticmethod
    async def get_all(
        db: AsyncSession,
        model: Type,
        filters: list | None = None,
        offset: int = 0,
        limit: int = 20,
        order_by=None,
    ):
        query = select(model)

        if filters:
            for condition in filters:
                query = query.where(condition)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    # 3️⃣ Create
    @staticmethod
    async def create(
        db: AsyncSession,
        model: Type,
        data: dict,
    ):
        try:
            obj = model(**data)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except Exception:
            await db.rollback()
            raise

    # 4️⃣ Update
    @staticmethod
    async def update(
        db: AsyncSession,
        obj: Any,
        data: dict,
    ):
        try:
            for field, value in data.items():
                setattr(obj, field, value)

            await db.commit()
            await db.refresh(obj)
            return obj
        except Exception:
            await db.rollback()
            raise

    # 5️⃣ Delete
    @staticmethod
    async def delete(
        db: AsyncSession,
        obj: Any,
    ):
        try:
            await db.delete(obj)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    # 6️⃣ Assign Role to User (RBAC)
    @staticmethod
    async def assign_role(
        db: AsyncSession,
        user_id: UUID,
        role_name: str,
    ):
        """
        Assign a role to a user.

        Responsibilities:
        - Fetch role by name
        - Prevent duplicate role assignment
        - Persist mapping

        Notes:
        - No permission logic here
        - Pure DB operation
        """

        try:
            # ✅ Fetch role
            result = await db.execute(
                select(Role).where(Role.name == role_name)
            )
            role = result.scalar_one_or_none()

            if not role:
                raise ValueError(f"Role '{role_name}' does not exist")

            # ✅ Prevent duplicate assignment
            existing = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                )
            )

            if existing.scalar_one_or_none():
                return  # Idempotent safe

            # ✅ Create mapping
            user_role = UserRole(
                user_id=user_id,
                role_id=role.id,
            )

            db.add(user_role)
            await db.commit()

        except Exception:
            await db.rollback()
            raise
