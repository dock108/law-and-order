"""Unit tests for database module."""

import os
from unittest import mock

import asyncpg
import pytest
import pytest_asyncio
from pi_auto.db import (
    close_connection_pool,
    execute_query,
    execute_transaction,
    get_connection_pool,
)


@pytest_asyncio.fixture
async def mock_pool():
    """Mock connection pool for testing."""
    pool_mock = mock.AsyncMock(spec=asyncpg.Pool)
    conn_mock = mock.AsyncMock(spec=asyncpg.Connection)
    pool_mock.acquire.return_value.__aenter__.return_value = conn_mock

    with mock.patch("pi_auto.db.engine._pool", pool_mock):
        yield pool_mock, conn_mock


@pytest.mark.asyncio
async def test_get_connection_pool():
    """Test get_connection_pool creates a pool if one doesn't exist."""
    # Ensure pool is None
    from pi_auto.db.engine import _pool

    if _pool:
        await close_connection_pool()

    # Mock create_pool to return an awaitable that gives our mock pool
    mock_pool = mock.AsyncMock(spec=asyncpg.Pool)

    async def mock_create_pool(*args, **kwargs):
        return mock_pool

    with mock.patch("asyncpg.create_pool", mock_create_pool):
        # Set environment variables for testing
        with mock.patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "test-key"},
        ):
            # Also need to patch the module-level variables
            with mock.patch(
                "pi_auto.db.engine.SUPABASE_URL", "https://example.supabase.co"
            ):
                with mock.patch("pi_auto.db.engine.SUPABASE_KEY", "test-key"):
                    pool = await get_connection_pool()

                    # Verify pool was created
                    assert pool is mock_pool

    # Clean up
    await close_connection_pool()


@pytest.mark.asyncio
async def test_get_connection_pool_error():
    """Test get_connection_pool raises an error if env vars are not set."""
    # Ensure pool is None
    with mock.patch("pi_auto.db.engine._pool", None):
        # Test with missing environment variables
        with mock.patch("pi_auto.db.engine.SUPABASE_URL", None):
            with mock.patch("pi_auto.db.engine.SUPABASE_KEY", None):
                with pytest.raises(ValueError):
                    await get_connection_pool()


@pytest.mark.asyncio
async def test_close_connection_pool():
    """Test close_connection_pool closes the pool."""
    # Create a mock pool
    mock_pool = mock.AsyncMock(spec=asyncpg.Pool)

    # Set it as the module pool
    with mock.patch("pi_auto.db.engine._pool", mock_pool):
        await close_connection_pool()

        # Verify the pool was closed
        mock_pool.close.assert_called_once()


@pytest.mark.asyncio
async def test_execute_query():
    """Test execute_query executes SQL query."""
    # Create mock objects
    mock_pool = mock.AsyncMock(spec=asyncpg.Pool)
    mock_conn = mock.AsyncMock(spec=asyncpg.Connection)
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetch.return_value = [{"id": 1, "name": "Test"}]

    # Set the mock pool as the module pool
    with mock.patch("pi_auto.db.engine._pool", mock_pool):
        result = await execute_query("SELECT * FROM test WHERE id = $1", 1)

        # Verify the query was executed
        mock_conn.fetch.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
        assert result == [{"id": 1, "name": "Test"}]


@pytest.mark.asyncio
async def test_execute_transaction():
    """Test execute_transaction executes multiple queries in a transaction."""
    # Create mock objects
    mock_pool = mock.AsyncMock(spec=asyncpg.Pool)
    mock_conn = mock.AsyncMock(spec=asyncpg.Connection)
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_transaction = mock.AsyncMock()
    mock_conn.transaction.return_value.__aenter__.return_value = mock_transaction

    queries = [
        ("INSERT INTO test VALUES ($1, $2)", [1, "Test"]),
        ("UPDATE test SET name = $1 WHERE id = $2", ["Updated", 1]),
    ]

    # Set the mock pool as the module pool
    with mock.patch("pi_auto.db.engine._pool", mock_pool):
        await execute_transaction(queries)

        # Check transaction was created
        mock_conn.transaction.assert_called_once()

        # Check both queries were executed
        assert mock_conn.execute.call_count == 2
        mock_conn.execute.assert_any_call("INSERT INTO test VALUES ($1, $2)", 1, "Test")
        mock_conn.execute.assert_any_call(
            "UPDATE test SET name = $1 WHERE id = $2", "Updated", 1
        )
