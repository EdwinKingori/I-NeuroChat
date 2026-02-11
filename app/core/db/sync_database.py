from sqlalchemy import create_engine
from core.config import get_settings

# Configuring synchronous database for alembic migrations
settings = get_settings()
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    future=True,
)
