"""
RBAC Seeder Logic
-----------------

Purpose:
Populate RBAC tables with initial roles & permissions.

Flow:
1️⃣ Insert Roles
2️⃣ Insert Permissions
3️⃣ Map Role → Permissions

Characteristics:
✅ Idempotent safe
✅ Logging enabled
✅ Transaction safe
"""

import uuid
from sqlalchemy.orm import Session

from app.core.db.sync_database import SessionLocal
from app.core.logging.route_logger import get_route_logger

from app.models import (
    users,
    user_memory,
    session,
    message,
    roles,
    permissions,
    user_roles,
    role_permissions,
)
from app.models.roles import Role
from app.models.permissions import Permission
from app.models.role_permissions import RolePermission

from app.core.seeds.seed_map_definitions import (
    ROLES,
    PERMISSIONS,
    ROLE_PERMISSIONS,
)

# ✅ Logger
logger = get_route_logger("rbac.seed")


def seed_rbac():
    """
    Execute RBAC seeding process.

    Safety:
    - Uses sync DB session
    - Wrapped in transaction
    """

    logger.info("🚀 Starting RBAC seed process")

    db: Session = SessionLocal()

    try:
        # ==================================================
        # 1️⃣ INSERT ROLES
        # ==================================================
        logger.info("Seeding roles...")

        role_map = {}

        for role_data in ROLES:
            existing_role = db.query(Role).filter_by(name=role_data["name"]).first()

            if existing_role:
                logger.debug("Role already exists → %s", role_data["name"])
                role_map[existing_role.name] = existing_role
                continue

            new_role = Role(
                id=uuid.uuid4(),
                name=role_data["name"],
                description=role_data["description"],
            )

            db.add(new_role)
            db.flush()  # Get PK without commit

            logger.info("Role created → %s", new_role.name)

            role_map[new_role.name] = new_role

        # ==================================================
        # 2️⃣ INSERT PERMISSIONS
        # ==================================================
        logger.info("Seeding permissions...")

        perm_map = {}

        for perm_data in PERMISSIONS:
            existing_perm = db.query(Permission).filter_by(name=perm_data["name"]).first()

            if existing_perm:
                logger.debug("Permission already exists → %s", perm_data["name"])
                perm_map[existing_perm.name] = existing_perm
                continue

            new_perm = Permission(
                id=uuid.uuid4(),
                name=perm_data["name"],
                description=perm_data.get("description"),
            )

            db.add(new_perm)
            db.flush()

            logger.info("Permission created → %s", new_perm.name)

            perm_map[new_perm.name] = new_perm

        # ==================================================
        # 3️⃣ MAP ROLE → PERMISSIONS
        # ==================================================
        logger.info("Mapping role → permissions...")

        for role_name, perm_list in ROLE_PERMISSIONS.items():
            role = role_map.get(role_name)

            if not role:
                logger.error("Role missing during mapping → %s", role_name)
                continue

            for perm_name in perm_list:
                perm = perm_map.get(perm_name)

                if not perm:
                    logger.error("Permission missing → %s", perm_name)
                    continue

                exists = db.query(RolePermission).filter_by(
                    role_id=role.id,
                    permission_id=perm.id,
                ).first()

                if exists:
                    logger.debug(
                        "Mapping exists → role=%s perm=%s",
                        role_name,
                        perm_name,
                    )
                    continue

                db.add(RolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                ))

                logger.info(
                    "Mapped → role=%s permission=%s",
                    role_name,
                    perm_name,
                )

        # ==================================================
        # ✅ COMMIT TRANSACTION
        # ==================================================
        db.commit()

        logger.info("✅ RBAC seeding completed successfully")

    except Exception as e:
        db.rollback()

        logger.exception("❌ RBAC seeding failed: %s", str(e))

    finally:
        db.close()

        logger.info("🔒 RBAC seed DB session closed")


if __name__ == "__main__":
    seed_rbac()
