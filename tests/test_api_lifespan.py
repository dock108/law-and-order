"""Tests for the FastAPI lifespan function."""

from unittest.mock import MagicMock, patch

import pytest
from pi_auto_api.main import lifespan


@pytest.mark.asyncio
async def test_lifespan_missing_settings():
    """Test lifespan events with missing settings."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Patch settings with missing values
    with patch("pi_auto_api.main.settings") as mock_settings:
        # Set both required settings to None to trigger warnings
        mock_settings.SUPABASE_URL = None
        mock_settings.SUPABASE_KEY = None

        # Patch logging
        with patch("pi_auto_api.main.logger") as mock_logger:
            # Use async with to execute the lifespan context manager
            cm = lifespan(mock_app)
            await cm.__aenter__()
            await cm.__aexit__(None, None, None)

            # Verify correct warning messages were logged
            mock_logger.warning.assert_any_call(
                "SUPABASE_URL is not set. The /readyz endpoint will fail."
            )
            mock_logger.warning.assert_any_call("SUPABASE_KEY is not set.")

            # Verify startup and shutdown logs
            mock_logger.info.assert_any_call("Starting up PI Auto API")
            mock_logger.info.assert_any_call("Shutting down PI Auto API")
