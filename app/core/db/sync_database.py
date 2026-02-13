from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
from app.core.config import get_settings
"""
✅ Synchronous Engine
 Used by:
 - Alembic migrations
 - Celery tasks
 - Sync scripts
"""
settings = get_settings()
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# ✅ Session Factory
SessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)