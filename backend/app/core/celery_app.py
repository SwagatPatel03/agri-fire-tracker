from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "agri_fire_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.services.fire_service",
        "app.tasks.cleanup",
    ],
)

celery_app.conf.beat_schedule = {
    # Fetch new fire data from NASA every hour
    "fetch-nasa-fires-hourly": {
        "task": "app.services.fire_service.fetch_and_process_nasa_fires",
        "schedule": crontab(minute=0),
    },
    # Mark old fires as inactive every day at midnight
    "cleanup-old-fires-daily": {
        "task": "app.tasks.cleanup.deactivate_old_fires",
        "schedule": crontab(hour=0, minute=30),
    },
}

celery_app.conf.timezone = "UTC"

# Prevent tasks from running forever
celery_app.conf.task_time_limit = 600       # Hard kill after 10 minutes
celery_app.conf.task_soft_time_limit = 300   # Soft warning after 5 minutes