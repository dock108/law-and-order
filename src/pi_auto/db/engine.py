"""Database engine and connection utilities."""

import os
from typing import Any, Optional

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_connection_pool() -> asyncpg.Pool:
    """Get or create a connection pool to the database.

    Returns:
        asyncpg.Pool: A connection pool to the Supabase PostgreSQL database.
    """
    global _pool
    if _pool is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            )

        # Extract database connection info from Supabase URL
        # Example format: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
        db_url = SUPABASE_URL.replace("supabase", "postgresql")

        # Create connection pool with Supabase API key in the connection parameters
        # This will be used for Row Level Security policies
        _pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=1,
            max_size=10,
            command_timeout=60,
            server_settings={"apikey": SUPABASE_KEY},
        )

    return _pool


async def close_connection_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def execute_query(query: str, *args: Any) -> list[asyncpg.Record]:
    """Execute a SQL query and return the results.

    Args:
        query: SQL query to execute
        *args: Query parameters

    Returns:
        List of database records
    """
    pool = await get_connection_pool()
    async with pool.acquire() as connection:
        return await connection.fetch(query, *args)


async def execute_transaction(queries: list[tuple[str, list[Any]]]) -> None:
    """Execute multiple SQL queries in a transaction.

    Args:
        queries: List of (query, params) tuples
    """
    pool = await get_connection_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            for query, params in queries:
                await connection.execute(query, *params)
