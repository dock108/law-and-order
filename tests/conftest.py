"""Pytest configuration file for the tests."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def db_url() -> str:
    """Get the database URL from environment variable, default for local testing."""
    # Use the same env var name as in CI for consistency
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://testuser:testpassword@localhost:5432/testdb",
    )
    # asyncpg needs postgresql:// not postgresql+asyncpg://
    return url.replace("+asyncpg", "")


# Mapping of test roles to user details
# Using fixed UUIDs from seed.sql for JWT claims
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
    },  # Example anon user
}


@pytest_asyncio.fixture
async def db_conn(db_url: str, request) -> AsyncGenerator[asyncpg.Connection, None]:
    """Yields an asyncpg connection connected AS the appropriate database role.

    Connects using the base role (lawyer, paralegal, client, anon)
    but sets JWT claims based on the specific marker (e.g., paralegal_a).
    Use like: @pytest.mark.parametrize("db_conn", ["paralegal_a"], indirect=True)
    """
    role_marker = request.param  # e.g., "paralegal_a"
    user_info = TEST_USERS.get(role_marker)
    if not user_info:
        pytest.fail(f"Unknown role marker in TEST_USERS: {role_marker}")

    # Determine the actual DATABASE role to connect as
    db_connect_role = user_info[
        "role"
    ]  # Get base role (e.g., 'paralegal') from user_info
    if db_connect_role not in ["lawyer", "paralegal", "client", "anon"]:
        # Basic safety check, could be more robust
        pytest.fail(f"Invalid database role derived: {db_connect_role}")

    # Base URL should not contain user/password
    base_db_url_parts = db_url.split("@")
    if len(base_db_url_parts) != 2:
        raise ValueError("db_url fixture needs adjustment for role-based connection")
    protocol_part = base_db_url_parts[0].split("://")[0]
    host_db_part = base_db_url_parts[1]

    # Construct DSN using the determined DATABASE role (e.g., 'paralegal')
    role_dsn = f"{protocol_part}://{db_connect_role}:testpassword@{host_db_part}"

    conn = None
    try:
        # Connect directly AS the determined database role
        conn = await asyncpg.connect(role_dsn)

        # Set the claims based on the specific role_marker (e.g., paralegal_a)
        # Use a simpler JWT claim with proper escaping
        jwt_claims = (
            f'{{"role": "{user_info["role"]}", '
            f'"email": "{user_info["email"]}", '
            f'"sub": "{user_info["sub"]}"}}'
        )

        # Use the simpler format and properly escape quotes
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
