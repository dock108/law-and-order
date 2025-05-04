"""Tests for CRUD operations."""

import pytest
import pytest_asyncio
from pi_auto.db import crud
from pi_auto.db.models import Base, Client
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite database for testing
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_engine():
    """Create an async SQLite in-memory engine for testing."""
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create an async session for the test database."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_create_client(async_session):
    """Test creating a client."""
    client_data = {
        "full_name": "Test Client",
        "email": "test@example.com",
        "phone": "555-555-5555",
        "address": "123 Test St",
    }

    new_client = await crud.create(async_session, Client, client_data)

    assert new_client.id is not None
    assert new_client.full_name == "Test Client"
    assert new_client.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_client(async_session):
    """Test getting a client by ID."""
    # Create a client
    client_data = {
        "full_name": "Get Test",
        "email": "get.test@example.com",
    }
    new_client = await crud.create(async_session, Client, client_data)

    # Get the client
    retrieved_client = await crud.get(async_session, Client, new_client.id)

    assert retrieved_client is not None
    assert retrieved_client.id == new_client.id
    assert retrieved_client.full_name == "Get Test"

    # Test getting a non-existent client
    nonexistent_client = await crud.get(async_session, Client, 9999)
    assert nonexistent_client is None


@pytest.mark.asyncio
async def test_get_all_clients(async_session):
    """Test getting all clients."""
    # Create multiple clients
    clients_data = [
        {"full_name": "Client 1", "email": "client1@example.com"},
        {"full_name": "Client 2", "email": "client2@example.com"},
        {"full_name": "Client 3", "email": "client3@example.com"},
    ]

    for data in clients_data:
        await crud.create(async_session, Client, data)

    # Get all clients
    clients = await crud.get_all(async_session, Client)

    assert len(clients) >= 3  # There might be clients from other tests
    assert any(client.full_name == "Client 1" for client in clients)
    assert any(client.full_name == "Client 2" for client in clients)
    assert any(client.full_name == "Client 3" for client in clients)


@pytest.mark.asyncio
async def test_update_client(async_session):
    """Test updating a client."""
    # Create a client
    client_data = {
        "full_name": "Update Test",
        "email": "before@example.com",
    }
    new_client = await crud.create(async_session, Client, client_data)

    # Update the client
    updated_data = {
        "email": "after@example.com",
        "phone": "555-123-4567",
    }
    updated_client = await crud.update(
        async_session, Client, new_client.id, updated_data
    )

    assert updated_client is not None
    assert updated_client.id == new_client.id
    assert updated_client.full_name == "Update Test"  # Unchanged
    assert updated_client.email == "after@example.com"  # Changed
    assert updated_client.phone == "555-123-4567"  # Added


@pytest.mark.asyncio
async def test_delete_client(async_session):
    """Test deleting a client."""
    # Create a client
    client_data = {
        "full_name": "Delete Test",
        "email": "delete@example.com",
    }
    new_client = await crud.create(async_session, Client, client_data)

    # Delete the client
    result = await crud.delete_record(async_session, Client, new_client.id)
    assert result is True

    # Verify the client is deleted
    deleted_client = await crud.get(async_session, Client, new_client.id)
    assert deleted_client is None

    # Test deleting a non-existent client
    result = await crud.delete_record(async_session, Client, 9999)
    assert result is False
