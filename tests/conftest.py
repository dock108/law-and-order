"""Pytest configuration file for the tests."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports needed for test setup & app context
from pi_auto.db.models import Base, Staff  # noqa: E402 # Import Base & Staff
from pi_auto.db.session import (  # noqa: E402
    get_db as get_db_original,  # Import original get_db
)
from pi_auto_api.auth import get_password_hash  # noqa: E402 # For test user fixtures
from pi_auto_api.config import settings  # noqa: E402
from pi_auto_api.main import app  # noqa: E402 # App instance

# Import test constants needed by fixtures
from tests.test_auth_login import TEST_STAFF_EMAIL, TEST_STAFF_PASSWORD  # noqa: E402

# --- SQLAlchemy Test Setup for most unit/integration tests ---
# Use in-memory SQLite for speed and isolation
# SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"
# Use file-based SQLite for potentially more stable test isolation
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine and session maker
test_engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields a SQLAlchemy async session for testing with clean tables.

    Ensures tables are created before and dropped after each test function.
    Ensures the session is rolled back after the test.
    """
    # Create tables before each test
    async with test_engine.begin() as conn:
        # print("Dropping tables...") # Debug print
        await conn.run_sync(Base.metadata.drop_all)  # Drop first for safety
        # print("Creating tables...") # Debug print
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # print(f"Yielding session {id(session)}...") # Debug print
        try:
            yield session
        finally:
            # print(f"Rolling back session {id(session)}...") # Debug print
            await session.rollback()
            # print(f"Closing session {id(session)}...") # Debug print
            await session.close()

    # Drop tables after each test (optional for in-memory)
    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


# Override get_db dependency globally for the test session
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override for get_db to use the test session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


app.dependency_overrides[get_db_original] = override_get_db

# --- Test User Fixtures (used by auth, spec, cors tests) ---


@pytest_asyncio.fixture(scope="function")
async def test_staff_user(db_session: AsyncSession) -> Staff:
    """Fixture to create a test staff user in the database."""
    hashed_password = get_password_hash(TEST_STAFF_PASSWORD)
    user = Staff(
        email=TEST_STAFF_EMAIL,
        username=TEST_STAFF_EMAIL,  # Assuming username is still required/present
        hashed_password=hashed_password,
        first_name="Test",
        last_name="Staff",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def inactive_test_staff_user(db_session: AsyncSession) -> Staff:
    """Fixture to create an inactive test staff user."""
    hashed_password = get_password_hash("anotherpassword")
    user = Staff(
        email="inactive.staff@example.com",
        username="inactive.staff@example.com",  # Assuming username required
        hashed_password=hashed_password,
        first_name="Inactive",
        last_name="Staff",
        is_active=False,  # Key difference
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# --- RLS Test Setup (Uses PostgreSQL, separate from above) ---


@pytest.fixture(scope="session")
def db_url() -> str:
    """Get the PostgreSQL database URL for RLS tests."""
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://testuser:testpassword@localhost:5432/testdb",  # Non-asyncpg
    )
    return url


# Mapping of test roles for RLS tests
TEST_USERS = {
    "lawyer": {
        "email": "lawyer@example.com",
        "role": "lawyer",
        "sub": "00000000-0000-0000-0000-000000000001",
    },
    "paralegal_a": {
        "email": "paralegal_a@example.com",
        "role": "paralegal",
        "sub": "00000000-0000-0000-0000-000000000002",
    },
    "paralegal_b": {
        "email": "paralegal_b@example.com",
        "role": "paralegal",
        "sub": "00000000-0000-0000-0000-000000000003",
    },
    "client_a": {
        "email": "client_a@example.com",
        "role": "client",
        "sub": "00000000-0000-0000-0000-000000000004",
    },
    "anon": {
        "email": "anon@example.com",
        "role": "anon",
        "sub": "00000000-0000-0000-0000-000000000000",
    },
}


@pytest_asyncio.fixture
async def db_conn(db_url: str, request) -> AsyncGenerator[asyncpg.Connection, None]:
    """Yields an asyncpg connection for RLS tests, connected AS the role.

    Use like: @pytest.mark.parametrize("db_conn", ["paralegal_a"], indirect=True)
    """
    role_marker = request.param
    user_info = TEST_USERS.get(role_marker)
    if not user_info:
        pytest.fail(f"Unknown role marker in TEST_USERS: {role_marker}")

    db_connect_role = user_info["role"]
    if db_connect_role not in ["lawyer", "paralegal", "client", "anon"]:
        pytest.fail(f"Invalid database role derived: {db_connect_role}")

    # Ensure db_url is compatible with asyncpg connection string format
    # Assuming db_url fixture returns postgresql://user:pass@host:port/db
    try:
        role_dsn = db_url.replace(
            "testuser:testpassword", f"{db_connect_role}:testpassword"
        )
    except Exception:
        pytest.fail(f"Could not construct DSN from db_url: {db_url}")

    conn = None
    try:
        conn = await asyncpg.connect(role_dsn)
        jwt_claims = (
            f'{{"role": "{user_info["role"]}", '
            f'"email": "{user_info["email"]}", '
            f'"sub": "{user_info["sub"]}"}}'
        )
        await conn.execute(f"SET LOCAL request.jwt.claims = '{jwt_claims}';")
        yield conn
    except asyncpg.exceptions.InvalidPasswordError:
        pytest.fail(
            f"Failed to connect as role '{db_connect_role}'. "
            f"Check password in migration."
        )
    except Exception as e:
        error_msg = (
            f"Failed to set up db_conn for role '{role_marker}' "
            f"(connecting as '{db_connect_role}'): {e}"
        )
        pytest.fail(error_msg)
    finally:
        if conn:
            await conn.close()


# --- General Test Client Fixture ---


@pytest_asyncio.fixture
async def async_client(monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing API endpoints.

    Uses the globally overridden get_db dependency.
    Ensures JWT_SECRET is set and overrides DATABASE_URL via settings.
    """
    # Override DATABASE_URL setting for this test client's lifespan
    # This ensures SQLAlchemy engine uses the SQLite DB
    monkeypatch.setattr(settings, "DATABASE_URL", SQLALCHEMY_TEST_DATABASE_URL)

    # Ensure JWT_SECRET is set for auth tests
    original_secret = settings.JWT_SECRET
    if not settings.JWT_SECRET:
        settings.JWT_SECRET = "test-secret-key-please-change"
        # print("\nWARNING: Using default test JWT_SECRET. Set via env for security.\n")

    # Run the test with the overridden settings and db dependency
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Restore original JWT secret if it was changed
    settings.JWT_SECRET = original_secret
