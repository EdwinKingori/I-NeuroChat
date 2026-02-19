# Ensuring alembic auto-delivers all tables
from app.core.db.database import Base
from .users import User
from .user_memory import UserMemory
from .session import ConversationSession
from .message import ChatMessage
from .session import ConversationSession
from .user_session import UserSession
from .permissions import Permission
from .role_permissions import RolePermission
from .roles import Role


"""
Central model import registry.

Purpose:
- Ensures all SQLAlchemy models are imported and registered
- Prevents mapper errors caused by partially-loaded models
"""

__all__ = ["Base", "User", "UserMemory", "ConversationSession", "ChatMessage", "UserSession", "Permission", "RolePermission", "Role"]
