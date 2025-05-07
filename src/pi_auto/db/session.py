"""SQLAlchemy session management for asynchronous operations."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from pi_auto_api.config import settings  # Assuming config is in pi_auto_api

logger = logging.getLogger(__name__)

# Global engine and sessionmaker (initialized lazily in get_db)
_async_engine = None
_AsyncSessionLocal = None


def _initialize_db():
    """Initializes the engine and sessionmaker if not already done."""
    global _async_engine, _AsyncSessionLocal
    if _async_engine is None:
        db_url = settings.DATABASE_URL
        # Log URL safely, hiding credentials
        protocol_end = db_url.find("://") + 3
        credential_start = db_url.find("@")
        log_db_url = db_url[:protocol_end] + "..." + db_url[credential_start:]
        logger.info(f"Initializing SQLAlchemy async engine for URL: {log_db_url}")
        if not db_url.startswith("postgresql+asyncpg") and not db_url.startswith(
            "sqlite+aiosqlite"
        ):
            logger.warning(
                f"DATABASE_URL '{db_url}' might not be asyncpg/aiosqlite compatible."
            )

        _async_engine = create_async_engine(
            db_url, echo=False
        )  # Set echo=True for SQL logging
        _AsyncSessionLocal = sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,  # Recommended for async to avoid implicit I/O
            autocommit=False,  # Recommended for async
        )


async def get_db() -> AsyncSession:
    """FastAPI dependency to get an async database session.

    Initializes engine/sessionmaker on first call.
    """
    _initialize_db()  # Ensure DB is initialized
    if _AsyncSessionLocal is None:
        # This should not happen if _initialize_db worked, but added as safeguard
        raise RuntimeError("Database session factory not initialized.")

    async with _AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # logger.exception("Rolling back session due to error")
            # # Optional: log error before rollback
            # await session.rollback()
            # # Rollback might happen automatically on __aexit__ depending on context
            raise
        finally:
            # logger.debug(f"Closing session {id(session)}")
            await session.close()


# Note: The main.py currently uses an asyncpg.Pool directly.
# This SQLAlchemy setup provides an alternative or complementary way to manage
# DB interactions, typically used by CRUD operations interacting with
# SQLAlchemy ORM models. If both are used, ensure they are managed coherently.
