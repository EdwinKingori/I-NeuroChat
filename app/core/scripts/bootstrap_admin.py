import asyncio
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import AsyncSessionLocal 
from app.core.logging.route_logger import get_route_logger

from app.models.users import User
from app.models.roles import Role
from app.models.user_roles import UserRole
from app.services.helpers.crud_helper import CRUDHelper

logger = get_route_logger("bootstrap.admin")


async def bootstrap_admin(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    update_existing: bool = True,
) -> str:
    """
  
    Bootstrap an initial admin user for local/testing environments (async).

    - Uses AsyncSession + CRUDHelper (same pattern as APIs)
    - Idempotent: won’t create duplicates
    - Ensures 'admin' role exists + is assigned
    - Compatible with current temp password hashing approach

    Run:
    python3 -m app.core.scripts.bootstrap_admin

    Creates (or updates) an admin user and ensures they have the 'admin' role.
    Returns the user_id (as str).
    """

    logger.info("Bootstrapping admin | username=%s email=%s", username, email)

    # 1) Ensure admin role exists
    result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    if not admin_role:
        raise RuntimeError(
            "Role 'admin' does not exist. Run RBAC seed first: "
            "`python3 -m app.core.seeds.rbac_seed`"
        )

    # 2) Find existing user by email OR username
    result = await db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    )
    user = result.scalar_one_or_none()

    # 3) Create or update user (keeps your current hashing convention)
    desired_data = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "hashed_password": f"temp_hash_{password}",  # 🔁 replace later with real hash
        "is_active": True,
    }

    if not user:
        user = await CRUDHelper.create(db, User, desired_data)
        logger.info("Created admin user | id=%s", user.id)
    elif update_existing:
        user = await CRUDHelper.update(db, user, desired_data)
        logger.info("Updated existing user | id=%s", user.id)
    else:
        logger.info("User exists (no update) | id=%s", user.id)

    # 4) Ensure mapping exists in user_roles
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == admin_role.id,
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        await CRUDHelper.create(
            db,
            UserRole,
            {"user_id": user.id, "role_id": admin_role.id},
        )
        logger.info("Assigned admin role | user_id=%s", user.id)
    else:
        logger.info("Admin role already assigned | user_id=%s", user.id)

    logger.info("✅ Admin bootstrap done | user_id=%s", user.id)
    return str(user.id)


async def main():
    # 🔧 Replace these with your testing values
    username = "DevEddAdmin"
    email = "freelancereddy254@gmail.com"
    first_name = "System"
    last_name = "Admin"
    password = "@Admin2026"  

    async with AsyncSessionLocal() as db:
        await bootstrap_admin(
            db,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            update_existing=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
