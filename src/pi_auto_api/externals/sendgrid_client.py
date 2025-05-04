"""Client for interacting with the SendGrid API.

This module provides a function to send emails via SendGrid using templates.
"""

import logging
from typing import Dict, Optional, Union

from fastapi import HTTPException, status
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To

from pi_auto_api.config import settings
from pi_auto_api.utils.email_renderer import render_email_template

logger = logging.getLogger(__name__)


async def send_mail(
    template_name: str,
    to_email: str,
    template_ctx: Dict[str, Union[str, Dict]],
    from_email: Optional[str] = None,
    subject: Optional[str] = None,
) -> str:
    """Render Jinja template and send via SendGrid.

    Args:
        template_name: Name of the template file to use
        to_email: Recipient email address
        template_ctx: Context variables for the template
        from_email: Sender email address (defaults to a no-reply address)
        subject: Email subject (defaults to a subject derived from template name)

    Returns:
        SendGrid message ID if successful

    Raises:
        ValueError: If SendGrid API key is not configured
        HTTPException: If the email fails to send
    """
    if not settings.SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY is not configured")
        raise ValueError("SendGrid API key is not configured")

    # Set default from_email if not provided
    if not from_email:
        from_email = "no-reply@pi-auto.example.com"

    # Set default subject if not provided
    if not subject:
        # Generate a subject based on template name
        # (remove .html and convert to title case)
        subject = template_name.replace(".html", "").replace("_", " ").title()

    try:
        # Render the template with provided context
        html_content = render_email_template(template_name, template_ctx)

        # Create the email message
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content),
        )

        # Send the email
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        # Extract message ID from response headers
        # SendGrid includes a message ID in X-Message-Id header
        message_id = None
        if hasattr(response, "headers") and "X-Message-Id" in response.headers:
            message_id = response.headers["X-Message-Id"]
        elif hasattr(response, "headers") and "x-message-id" in response.headers:
            message_id = response.headers["x-message-id"]

        # Log success
        logger.info(f"Email sent successfully to {to_email}: {template_name}")

        # Return the message ID if available, otherwise return status code
        return message_id or str(response.status_code)

    except FileNotFoundError as e:
        # Handle template not found
        logger.error(f"Template not found: {template_name}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email template not found: {template_name}",
        ) from e
    except Exception as e:
        # Handle other errors
        logger.error(f"Error sending email to {to_email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        ) from e
