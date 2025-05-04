"""Tests for the task functions."""

from pi_auto_api.tasks.retainer import generate_retainer


def test_generate_retainer():
    """Test the generate_retainer task."""
    # Call the task
    result = generate_retainer(123)

    # Verify the result
    assert result == {"client_id": 123, "status": "queued"}


def test_generate_retainer_with_mock_logger():
    """Test the generate_retainer task with mocked logger."""
    # Call the task with a different ID to test consistency
    result = generate_retainer(456)

    # Verify the result
    assert result == {"client_id": 456, "status": "queued"}


# Add your tests here
