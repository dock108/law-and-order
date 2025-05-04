"""Tests for the FastAPI lifespan function database pool handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pi_auto_api.main import lifespan


@pytest.mark.asyncio
async def test_db_pool_close_called():
    """Test that db_pool.close() is called during lifespan exit when pool exists."""
    # Create a mock FastAPI app and pool
    mock_app = MagicMock()
    mock_pool = AsyncMock()

    # Create a patched module-level db_pool that already contains our mock
    with patch("pi_auto_api.main.db_pool", mock_pool):
        # Execute lifespan context manager
        cm = lifespan(mock_app)
        await cm.__aenter__()
        await cm.__aexit__(None, None, None)

        # Verify pool.close was called
        mock_pool.close.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_with_db_pool_initialization_error():
    """Test lifespan events with database pool initialization error."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Patch settings and asyncpg
    with patch("pi_auto_api.main.settings") as mock_settings:
        mock_settings.SUPABASE_URL = "postgresql://user:pass@localhost:5432/db"
        mock_settings.SUPABASE_KEY = "test-key"

        with patch("pi_auto_api.main.asyncpg.create_pool") as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection error")

            with patch("pi_auto_api.main.db_pool", None):
                with patch("pi_auto_api.main.logger") as mock_logger:
                    # Execute the lifespan context manager
                    cm = lifespan(mock_app)
                    await cm.__aenter__()

                    # Verify error was logged
                    error_msg = "Failed to initialize database connection pool:"
                    error_msg += " Connection error"
                    mock_logger.error.assert_any_call(error_msg)

                    # Clean up
                    await cm.__aexit__(None, None, None)

                    # We don't try to close the pool in this case as it wasn't created
