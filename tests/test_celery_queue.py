"""Tests for the Celery task queue."""

import pytest
from pi_auto_api.tasks import app as celery_app
from pi_auto_api.tasks.retainer import generate_retainer


@pytest.fixture
def celery_config():
    """Configure Celery for testing."""
    # Use in-memory broker for testing
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "memory://"
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    return celery_app


@pytest.mark.asyncio
async def test_generate_retainer_task():
    """Test the generate_retainer task returns the expected result."""
    # Call the task function directly
    response = generate_retainer(1)

    # Assert the expected response
    assert response == {"client_id": 1, "status": "queued"}
