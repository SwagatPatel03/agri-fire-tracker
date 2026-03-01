# Celery is a distributed task queue that allows you to run tasks in the background
from celery import Celery
# crontab is used to schedule tasks at specific times
from celery.schedules import crontab
from app.core.config import settings

# 1. Initialize the Celery App
# We name it "agri-fire-worker" and point both the broker and result backend to Redis
celery_app = Celery(
    "agri_fire_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # Tell Celery which files to look inside for @shared_task decorators
    include=["app.services.fire_service"]
)

# 2. Configure Celery Beat (The Scheduler)
# This tells Celery: "Run the function fetch_and_process_nasa_fires every hour"
celery_app.conf.beat_schedule = {
    'fetch-nasa-fires-hourly': {
        # The exact path to the func we want to run
        'task': 'app.services.fire_service.fetch_and_process_nasa_fires',
        # crontab(minute=0) means "run at the 0th minute of every hour" e.g., 1:00, 2:00, 3:00)
        'schedule': crontab(minute=0),
    },
}

# Ensure timestamps match a standard UTC time
celery_app.conf.timezone = 'UTC'