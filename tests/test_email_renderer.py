"""Tests for the email template renderer."""

from unittest.mock import patch

import pytest
from jinja2.exceptions import TemplateError
from pi_auto_api.utils.email_renderer import render_email_template

# Test data
TEST_CONTEXT = {
    "client": {
        "full_name": "John Doe",
        "email": "john@example.com",
    },
    "support_email": "support@example.com",
    "support_phone": "555-123-4567",
}


@pytest.fixture
def mock_template_dir(tmp_path):
    """Create a temporary template directory with test templates."""
    templates_dir = tmp_path / "email_templates"
    templates_dir.mkdir()

    # Create a valid test template
    valid_template = templates_dir / "valid_template.html"
    valid_template.write_text(
        """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Hello {{ client.full_name }}!</h1>
        <p>Contact us at {{ support_email }} or {{ support_phone }}</p>
        <p>Current year: {{ current_year }}</p>
    </body>
    </html>
    """
    )

    # Create a template with syntax error
    invalid_template = templates_dir / "invalid_template.html"
    invalid_template.write_text(
        """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Hello {{ client.full_name !!</h1>
    </body>
    </html>
    """
    )

    yield templates_dir


@patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR")
def test_render_valid_template(mock_templates_dir, mock_template_dir):
    """Test rendering a valid email template."""
    mock_templates_dir.return_value = mock_template_dir
    mock_templates_dir.__truediv__.return_value = (
        mock_template_dir / "valid_template.html"
    )

    # Patch the actual directory
    with patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR", mock_template_dir):
        result = render_email_template("valid_template.html", TEST_CONTEXT)

    # Check that template was rendered correctly
    assert "Hello John Doe!" in result
    assert "Contact us at support@example.com or 555-123-4567" in result
    assert (
        "Current year: 2023" in result
        or "Current year: 2024" in result
        or "Current year: 2025" in result
    )


@patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR")
def test_template_not_found(mock_templates_dir, mock_template_dir):
    """Test handling of a non-existent template file."""
    mock_templates_dir.return_value = mock_template_dir
    mock_templates_dir.__truediv__.return_value = mock_template_dir / "nonexistent.html"

    # Patch the actual directory
    with patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR", mock_template_dir):
        with pytest.raises(
            FileNotFoundError, match="Email template nonexistent.html not found"
        ):
            render_email_template("nonexistent.html", TEST_CONTEXT)


@patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR")
def test_template_syntax_error(mock_templates_dir, mock_template_dir):
    """Test handling of a template with syntax errors."""
    mock_templates_dir.return_value = mock_template_dir
    mock_templates_dir.__truediv__.return_value = (
        mock_template_dir / "invalid_template.html"
    )

    # Patch the actual directory
    with patch("pi_auto_api.utils.email_renderer.TEMPLATES_DIR", mock_template_dir):
        with pytest.raises(TemplateError):
            render_email_template("invalid_template.html", TEST_CONTEXT)


def test_current_year_added_to_context():
    """Test that current_year is added to the context if not present."""
    context = {"test": "value"}

    with (
        patch("pi_auto_api.utils.email_renderer.os.path.exists", return_value=True),
        patch("pi_auto_api.utils.email_renderer.Environment") as mock_env,
    ):
        # Mock the Environment and Template objects
        mock_template = mock_env.return_value.get_template.return_value

        # Call the function
        render_email_template("template.html", context)

        # Get the context that was passed to render
        render_kwargs = mock_template.render.call_args[1]

        # Verify current_year was added
        assert "current_year" in render_kwargs
        from datetime import datetime

        assert render_kwargs["current_year"] == datetime.now().year
