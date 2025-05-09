"""Alembic environment configuration."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import our models for Alembic to use (must be after path setup)
import pi_auto.db.models  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import metadata from models
target_metadata = pi_auto.db.models.Base.metadata

# Get database connection URL from environment variable
supabase_url = os.getenv("SUPABASE_URL")
# Ensure the URL starts with postgresql+asyncpg:// for async engine
if supabase_url and "postgresql" in supabase_url:
    if "+asyncpg" not in supabase_url:
        db_url = supabase_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        db_url = supabase_url
else:
    db_url = None  # Or a default like "postgresql+asyncpg://user:pass@host/db"

# Replace the sqlalchemy.url in the config with the environment variable
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in the context of a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Ensure the config section uses the potentially modified db_url
    engine_config = config.get_section(config.config_ini_section)

    connectable = async_engine_from_config(
        engine_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Driver is inferred from the URL prefix
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    # Use asyncio.run() for direct script execution compatibility
    asyncio.run(run_migrations_online())
