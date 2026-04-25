"""Scheduled cleanup tasks for data retention."""

from datetime import datetime, timezone, timedelta

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.fire import Fire

logger = get_logger(__name__)


@celery_app.task
def deactivate_old_fires(max_age_days: int = 7):
    """Mark fires older than max_age_days as inactive."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        count = db.query(Fire).filter(
            Fire.is_active == True,  # noqa: E712
            Fire.detected_at < cutoff,
        ).update({"is_active": False})

        db.commit()
        logger.info(f"Deactivated {count} fires older than {max_age_days} days")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()
