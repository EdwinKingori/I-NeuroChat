from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from app.core.celery.celery_app import celery
from app.core.db.sync_database import SessionLocal
from app.models.users import User



@celery.task
def deactivate_stale_users():
    """
    Background task:
    Deactivates users inactive for 90 days.

    Runs:
    - Daily via Celery Beat

    Logic:
    - last_login older than threshold
    - Only active users
    """

    db = SessionLocal()

    try:
        threshold = timezone.now() - timedelta(days=90)

        result = db.execute(
            update(User)
            .where(User.last_login < threshold)
            .where(User.is_active == True)
            .values(is_active=False)
        )

        db.commit()

        return f"Deactivated {result.rowcount} stale users"

    finally:
        db.close()
