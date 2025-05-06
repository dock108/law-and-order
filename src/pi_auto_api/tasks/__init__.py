"""Celery task queue configuration and tasks for background processing."""

from celery import Celery
from celery.schedules import crontab

from pi_auto_api.config import settings

app = Celery(
    "pi_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "pi_auto_api.tasks.retainer",
        "pi_auto_api.tasks.insurance_notice",
        "pi_auto_api.tasks.medical_records",
    ],
)
app.conf.task_default_queue = "default"

# Configure Beat schedule
# Note: Using 2:00 AM Eastern Time (America/New_York)
app.conf.beat_schedule = {
    "nightly-medical-record-request": {
        "task": "send_medical_record_requests",
        "schedule": crontab(hour=2, minute=0),
    }
}
