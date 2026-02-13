from celery import Celery 
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "ineuro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# ✅ Celery Configuration
celery.conf.update(
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
)

# ✅ CELERY BEAT SCHEDULE
celery.conf.beat_schedule = {
    "deactivate-stale-users-daily": {
        "task": "app.tasks.user_tasks.deactivate_stale_users",
        "schedule": crontab(hour=3, minute=0),
    },
}