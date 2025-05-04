"""Celery tasks for the PI Automation API.

This module contains Celery tasks for background processing.
"""

import logging

from celery import Celery

# Configure logging
logger = logging.getLogger(__name__)

# Configure Celery
app = Celery(
    "pi_auto_api",
    broker="pyamqp://guest@localhost//",  # Default RabbitMQ URL
)

# Configure Celery settings
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    task_track_started=True,
)


@app.task(name="tasks.generate_retainer")
def generate_retainer(client_id: int) -> str:
    """Generate a retainer agreement for a client.

    This is a stub task that will be implemented in the future.

    Args:
        client_id: The ID of the client to generate a retainer for

    Returns:
        A message indicating the task was executed
    """
    logger.info(f"Generating retainer for client {client_id}")

    # This is a stub for now and will be implemented in the future
    return f"Retainer generation queued for client {client_id}"
