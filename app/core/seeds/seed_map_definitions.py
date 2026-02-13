"""
RBAC Seed Definitions
---------------------

Contains static seed configuration for:

✅ Roles
✅ Permissions
✅ Role → Permission mappings

This file MUST remain logic-free.
Only declarative seed data belongs here.
"""

# ==========================================================
# ✅ ROLES
# ----------------------------------------------------------
# System roles recognized by the application.
# ==========================================================
ROLES = [
    {"name": "admin", "description": "System administrator"},
    {"name": "support", "description": "Customer support role"},
    {"name": "user", "description": "Default application user"},
]


# ==========================================================
# ✅ PERMISSIONS
# ----------------------------------------------------------
# Atomic capabilities used for RBAC enforcement.
# ==========================================================
PERMISSIONS = [
    {"name": "users.read", "description": "View users"},
    {"name": "users.activate", "description": "Activate user accounts"},
    {"name": "users.promote", "description": "Promote users to roles"},
]


# ==========================================================
# ✅ ROLE → PERMISSIONS MAP
# ----------------------------------------------------------
# Defines which permissions belong to each role.
# ==========================================================
ROLE_PERMISSIONS = {
    "admin": [
        "users.read",
        "users.activate",
        "users.promote",
    ],
    "support": [
        "users.read",
    ],
    "user": [],
}
