"""Tests for Celery tasks."""

from unittest.mock import patch

from pi_auto_api.tasks import generate_retainer


def test_generate_retainer():
    """Test the generate_retainer task."""
    # Call the task
    result = generate_retainer(123)

    # Verify the result
    assert "Retainer generation queued for client 123" == result


def test_generate_retainer_with_mock_logger():
    """Test the generate_retainer task with mocked logger."""
    # Mock the logger
    with patch("pi_auto_api.tasks.logger") as mock_logger:
        # Call the task
        result = generate_retainer(456)

        # Verify the result
        assert "Retainer generation queued for client 456" == result

        # Verify logger was called
        mock_logger.info.assert_called_once_with("Generating retainer for client 456")
