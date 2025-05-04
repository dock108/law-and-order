"""Celery task queue configuration and tasks for background processing."""

from celery import Celery

from pi_auto_api.config import settings

app = Celery(
    "pi_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["pi_auto_api.tasks.retainer"],
)
app.conf.task_default_queue = "default"
