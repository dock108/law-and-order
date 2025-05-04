"""Tests for the Celery app configuration and task discovery."""

import pytest
from pi_auto_api.tasks import app as celery_app
from pi_auto_api.tasks.retainer import generate_retainer


@pytest.fixture
def celery_config():
    """Configure Celery for testing (minimal config)."""
    # Use in-memory broker just to avoid connection errors during config checks
    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "memory://"
    # Keep eager mode off for this type of test
    celery_app.conf.task_always_eager = False
    return celery_app


# Remove @pytest.mark.asyncio as this test is now synchronous
def test_generate_retainer_task_registered(celery_config):
    """Test that the generate_retainer task is registered with Celery."""
    assert "generate_retainer" in celery_config.tasks
    # Check if the imported function matches the registered task
    assert generate_retainer.name == "generate_retainer"
    registered_task = celery_config.tasks.get("generate_retainer")
    assert registered_task is not None
    # Optionally, check if it points to the correct function (tricky with proxies)
    # assert registered_task.run == generate_retainer
