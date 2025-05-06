"""Pytest configuration for integration tests."""

import asyncio
import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List
from unittest.mock import MagicMock, patch

import asyncpg
import pytest
import pytest_asyncio
from celery.result import AsyncResult
from fastapi import FastAPI
from httpx import AsyncClient

from pi_auto_api.config import settings


@pytest.fixture(scope="session")
def app_settings():
    """Configure test-specific application settings."""
    # Store original settings
    original_settings = {}
    for field in dir(settings):
        if field.isupper() and not field.startswith("_"):
            original_settings[field] = getattr(settings, field)

    # Override with test settings
    settings.DOCASSEMBLE_URL = "http://mock-docassemble:5000"
    settings.DOCUSIGN_BASE_URL = "https://mock-docusign.com"
    settings.DOCUSIGN_ACCOUNT_ID = "mock-account-id"
    settings.DOCUSIGN_INTEGRATOR_KEY = "mock-integrator-key"
    settings.DOCUSIGN_USER_ID = "mock-user-id"
    settings.DOCUSIGN_PRIVATE_KEY = "./tests/integration/resources/mock_private_key.pem"
    settings.TWILIO_ACCOUNT_SID = "mock-twilio-sid"
    settings.TWILIO_AUTH_TOKEN = "mock-twilio-token"
    settings.SENDGRID_API_KEY = "mock-sendgrid-key"
    settings.REDIS_URL = "memory://"
    settings.SUPABASE_URL = "postgresql://testuser:testpassword@localhost:5432/testdb"

    yield settings

    # Restore original settings
    for field, value in original_settings.items():
        setattr(settings, field, value)


@pytest.fixture
def fake_celery_eager():
    """Configure Celery to execute tasks eagerly (immediately)."""
    with patch("pi_auto_api.celery_app.app.task") as mock_task:
        # Create a decorator that replaces the celery task decorator
        def eager_task_decorator(*args, **kwargs):
            def decorator(func):
                # Mock the delay method to call the task directly
                async def mock_delay(*task_args, **task_kwargs):
                    # Return AsyncResult mock with task_id
                    result = AsyncResult("mock-task-id")
                    result.id = "mock-task-id"

                    # If the function is async, await it
                    if asyncio.iscoroutinefunction(func):
                        await func(*task_args, **task_kwargs)
                    else:
                        func(*task_args, **task_kwargs)

                    return result

                # Add the delay mock to the original function
                func.delay = mock_delay
                return func

            return decorator

        # Make the mock act like the original decorator
        mock_task.side_effect = eager_task_decorator
        yield mock_task


@pytest.fixture
def mock_docassemble():
    """Mock the Docassemble API client."""
    with (
        patch(
            "pi_auto_api.externals.docassemble.generate_letter"
        ) as mock_generate_letter,
        patch(
            "pi_auto_api.externals.docassemble.generate_retainer_pdf"
        ) as mock_generate_retainer,
    ):
        # Configure the mocks
        async def mock_pdf_generator(*args, **kwargs):
            """Return mock PDF bytes."""
            return b"%PDF-1.7\nMock PDF content for testing\n%%EOF"

        mock_generate_letter.side_effect = mock_pdf_generator
        mock_generate_retainer.side_effect = mock_pdf_generator

        yield {
            "generate_letter": mock_generate_letter,
            "generate_retainer_pdf": mock_generate_retainer,
        }


@pytest.fixture
def mock_docusign():
    """Mock the DocuSign API client."""
    with (
        patch("pi_auto_api.externals.docusign.send_envelope") as mock_send,
        patch("pi_auto_api.externals.docusign._get_docusign_api_client") as mock_client,
    ):
        mock_api_client = MagicMock()
        mock_client.return_value = mock_api_client

        # Configure the mock to return a successful envelope ID
        async def mock_send_envelope(*args, **kwargs):
            """Return a mock envelope ID."""
            return f"mock-envelope-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        mock_send.side_effect = mock_send_envelope

        yield {"send_envelope": mock_send, "api_client": mock_api_client}


@pytest.fixture
def mock_twilio():
    """Mock the Twilio API client for SMS and fax."""
    with (
        patch("pi_auto_api.externals.twilio_client.send_sms") as mock_sms,
        patch("pi_auto_api.externals.twilio_client.send_fax") as mock_fax,
    ):
        # Configure the mocks
        async def mock_sms_sender(*args, **kwargs):
            """Return a mock SMS SID."""
            return f"mock-sms-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        async def mock_fax_sender(*args, **kwargs):
            """Return a mock fax SID."""
            return f"mock-fax-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        mock_sms.side_effect = mock_sms_sender
        mock_fax.side_effect = mock_fax_sender

        yield {"send_sms": mock_sms, "send_fax": mock_fax}


@pytest.fixture
def mock_sendgrid():
    """Mock the SendGrid API client for emails."""
    with patch("pi_auto_api.externals.sendgrid_client.send_mail") as mock_send:
        # Configure the mock
        async def mock_email_sender(*args, **kwargs):
            """Return a mock message ID."""
            return f"mock-email-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        mock_send.side_effect = mock_email_sender

        yield mock_send


@pytest.fixture
def mock_storage():
    """Mock the storage utilities."""
    with (
        patch("pi_auto_api.utils.storage.upload_file") as mock_upload,
        patch("pi_auto_api.utils.storage.get_file_content") as mock_get,
    ):
        # Configure the mocks
        async def mock_upload_file(*args, **kwargs):
            """Return a mock file URL."""
            filename = args[1] if len(args) > 1 else "mock-file"
            return f"https://mock-storage.com/{filename}"

        async def mock_get_file_content(*args, **kwargs):
            """Return mock file content."""
            return b"Mock file content for testing"

        mock_upload.side_effect = mock_upload_file
        mock_get.side_effect = mock_get_file_content

        yield {"upload_file": mock_upload, "get_file_content": mock_get}


@pytest_asyncio.fixture
async def db_session(app_settings) -> AsyncGenerator[asyncpg.Connection, None]:
    """Create a database connection with transaction rollback."""
    # Connect to the database
    conn = await asyncpg.connect(settings.SUPABASE_URL)

    # Start a transaction
    transaction = conn.transaction()
    await transaction.start()

    yield conn

    # Rollback the transaction
    await transaction.rollback()

    # Close the connection
    await conn.close()


@asynccontextmanager
async def override_dependencies(app: FastAPI):
    """Override dependencies for testing."""
    # This simulates the app's lifespan for testing
    yield


@pytest_asyncio.fixture
async def test_client(
    app_settings,
    fake_celery_eager,
    mock_docassemble,
    mock_docusign,
    mock_twilio,
    mock_sendgrid,
    mock_storage,
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with mocked dependencies."""
    from pi_auto_api.main import app

    # Store original router lifespan context
    original_lifespan_context = app.router.lifespan_context

    # Override lifespan to avoid actual service connections
    app.router.lifespan_context = override_dependencies(app)

    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Restore original router lifespan context
    app.router.lifespan_context = original_lifespan_context


@pytest.fixture
def time_machine():
    """Fixture to manipulate time for testing."""
    with patch("datetime.datetime") as mock_datetime:
        # Configure the mock
        mock_datetime.now.return_value = datetime.datetime(2025, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime.datetime(
            *args, **kwargs
        )

        yield mock_datetime


@pytest.fixture
def run_cron_task():
    """Fixture to run a scheduled Celery task immediately."""

    def _run_task(task_func, *args, **kwargs):
        """Run a task function with the given arguments."""
        # If the function is async, run it in the event loop
        if asyncio.iscoroutinefunction(task_func):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(task_func(*args, **kwargs))
        else:
            return task_func(*args, **kwargs)

    return _run_task


@pytest.fixture
def fake_doc_rows():
    """Generate fake document rows for testing."""

    def _generate_rows(incident_id: int, doc_types: List[str]) -> List[dict]:
        """Generate document rows for the given incident and types."""
        fake_rows = []
        for i, doc_type in enumerate(doc_types):
            fake_rows.append(
                {
                    "id": i + 1,
                    "incident_id": incident_id,
                    "type": doc_type,
                    "url": f"https://mock-storage.com/{doc_type}_{incident_id}.pdf",
                    "status": "completed",
                    "created_at": datetime.datetime.now() - datetime.timedelta(days=i),
                    "envelope_id": (
                        f"mock-envelope-{i}"
                        if "retainer" in doc_type or "disbursement" in doc_type
                        else None
                    ),
                    "amount": 1000.0 if "medical_bill" in doc_type else None,
                }
            )
        return fake_rows

    return _generate_rows
