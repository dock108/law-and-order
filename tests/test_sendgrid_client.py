"""Tests for SendGrid email client functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pi_auto_api.externals.sendgrid_client import send_mail
from sendgrid.helpers.mail import Mail

# Test data
TEST_EMAIL = "client@example.com"
TEST_TEMPLATE = "test_template.html"
TEST_CONTEXT = {
    "client": {
        "full_name": "John Doe",
        "email": TEST_EMAIL,
    },
    "support_email": "support@example.com",
    "support_phone": "555-123-4567",
}


@pytest.fixture
def mock_template_path(tmp_path):
    """Create a temporary test template file."""
    templates_dir = tmp_path / "email_templates"
    templates_dir.mkdir()

    # Create a simple test template
    template_content = """
    <html>
    <body>
    <h1>Test Email</h1>
    <p>Hello {{ client.full_name }}!</p>
    <p>Contact: {{ support_email }}</p>
    <p>Year: {{ current_year }}</p>
    </body>
    </html>
    """

    template_file = templates_dir / TEST_TEMPLATE
    template_file.write_text(template_content)

    # Patch the template directory path
    with patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR", templates_dir):
        yield template_file


@pytest.mark.asyncio
@patch("pi_auto_api.externals.sendgrid_client.settings")
@patch("pi_auto_api.externals.sendgrid_client.SendGridAPIClient")
@patch("pi_auto_api.externals.sendgrid_client.render_email_template")
async def test_send_mail_success(
    mock_render, mock_sendgrid, mock_settings, mock_template_path
):
    """Test successful email sending."""
    # Configure mocks
    mock_settings.SENDGRID_API_KEY = "test_api_key"

    # Mock the render_email_template to return a known HTML string
    html_content = (
        "<html><body>"
        "<p>Hello John Doe!</p>"
        "<p>Contact: support@example.com</p>"
        "<p>Year: 2023</p>"
        "</body></html>"
    )
    mock_render.return_value = html_content

    # Set up SendGrid mock
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {"X-Message-Id": "test-message-id-123"}
    mock_client_instance.send.return_value = mock_response
    mock_sendgrid.return_value = mock_client_instance

    # Call the function
    result = await send_mail(
        template_name=TEST_TEMPLATE, to_email=TEST_EMAIL, template_ctx=TEST_CONTEXT
    )

    # Assertions
    assert result == "test-message-id-123"

    # Check SendGrid client was initialized with API key
    mock_sendgrid.assert_called_once_with("test_api_key")

    # Check render_email_template was called with correct args
    mock_render.assert_called_once_with(TEST_TEMPLATE, TEST_CONTEXT)

    # Check send was called
    mock_client_instance.send.assert_called_once()

    # Validate the Mail object
    mail_obj = mock_client_instance.send.call_args[0][0]
    assert isinstance(mail_obj, Mail)
    assert mail_obj.from_email.email == "no-reply@pi-auto.example.com"
    assert str(mail_obj.subject) == "Test Template"


@pytest.mark.asyncio
@patch("pi_auto_api.externals.sendgrid_client.settings")
async def test_send_mail_missing_api_key(mock_settings):
    """Test error when SendGrid API key is not configured."""
    # Configure mock
    mock_settings.SENDGRID_API_KEY = None

    # Call the function and expect error
    with pytest.raises(ValueError, match="SendGrid API key is not configured"):
        await send_mail(
            template_name=TEST_TEMPLATE, to_email=TEST_EMAIL, template_ctx=TEST_CONTEXT
        )


@pytest.mark.asyncio
@patch("pi_auto_api.externals.sendgrid_client.settings")
@patch("pi_auto_api.externals.sendgrid_client.render_email_template")
async def test_send_mail_template_not_found(mock_render, mock_settings):
    """Test error when template file is not found."""
    # Configure mocks
    mock_settings.SENDGRID_API_KEY = "test_api_key"
    mock_render.side_effect = FileNotFoundError("Template not found")

    # Call the function and expect error
    with pytest.raises(HTTPException) as exc_info:
        await send_mail(
            template_name="non_existent_template.html",
            to_email=TEST_EMAIL,
            template_ctx=TEST_CONTEXT,
        )

    assert exc_info.value.status_code == 500
    assert "Email template not found" in exc_info.value.detail


@pytest.mark.asyncio
@patch("pi_auto_api.externals.sendgrid_client.settings")
@patch("pi_auto_api.externals.sendgrid_client.render_email_template")
@patch("pi_auto_api.externals.sendgrid_client.SendGridAPIClient")
async def test_send_mail_sendgrid_error(mock_sendgrid, mock_render, mock_settings):
    """Test handling of SendGrid API errors."""
    # Configure mocks
    mock_settings.SENDGRID_API_KEY = "test_api_key"
    mock_render.return_value = "<html><body>Test email content</body></html>"

    # Set up SendGrid mock to raise an exception
    mock_client_instance = MagicMock()
    mock_client_instance.send.side_effect = Exception("SendGrid API error")
    mock_sendgrid.return_value = mock_client_instance

    # Call the function and expect error
    with pytest.raises(HTTPException) as exc_info:
        await send_mail(
            template_name=TEST_TEMPLATE, to_email=TEST_EMAIL, template_ctx=TEST_CONTEXT
        )

    assert exc_info.value.status_code == 500
    assert "Failed to send email" in exc_info.value.detail


@pytest.mark.asyncio
@patch("pi_auto_api.externals.sendgrid_client.settings")
@patch("pi_auto_api.externals.sendgrid_client.SendGridAPIClient")
@patch("pi_auto_api.externals.sendgrid_client.render_email_template")
async def test_send_mail_custom_from_and_subject(
    mock_render, mock_sendgrid, mock_settings, mock_template_path
):
    """Test sending email with custom from address and subject."""
    # Configure mocks
    mock_settings.SENDGRID_API_KEY = "test_api_key"

    # Mock the template rendering
    html_content = "<html><body>Test email content</body></html>"
    mock_render.return_value = html_content

    # Set up SendGrid mock
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {"X-Message-Id": "test-message-id-123"}
    mock_client_instance.send.return_value = mock_response
    mock_sendgrid.return_value = mock_client_instance

    custom_from = "custom@example.com"
    custom_subject = "Custom Email Subject"

    # Call the function
    await send_mail(
        template_name=TEST_TEMPLATE,
        to_email=TEST_EMAIL,
        template_ctx=TEST_CONTEXT,
        from_email=custom_from,
        subject=custom_subject,
    )

    # Assertions
    mail_obj = mock_client_instance.send.call_args[0][0]
    assert mail_obj.from_email.email == custom_from
    assert str(mail_obj.subject) == custom_subject
