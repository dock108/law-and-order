"""Client for interacting with the Twilio API.

This module provides functions to send SMS messages and faxes via Twilio.
"""

import logging
import time
from typing import Optional

from fastapi import HTTPException, status
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)


# Initialize the Twilio client
def get_twilio_client() -> Client:
    """Returns a configured Twilio client instance.

    Raises:
        ValueError: If Twilio credentials are not configured
    """
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN]):
        logger.error("Twilio credentials not configured")
        raise ValueError("Twilio credentials not configured")

    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_sms(
    to: str, body: str, from_number: Optional[str] = None, max_attempts: int = 3
) -> str:
    """Sends SMS message via Twilio with retry logic.

    Args:
        to: Recipient phone number in E.164 format (e.g. +15551234567)
        body: Message content
        from_number: Sender phone number (defaults to TWILIO_SMS_FROM)
        max_attempts: Maximum number of retry attempts for transient errors

    Returns:
        Twilio message SID

    Raises:
        ValueError: If Twilio configuration is missing
        HTTPException: If message sending fails after retries
    """
    if not from_number:
        from_number = settings.TWILIO_SMS_FROM

    if not from_number:
        logger.error("TWILIO_SMS_FROM not configured")
        raise ValueError("Twilio SMS sender number not configured")

    client = get_twilio_client()
    attempt = 0
    backoff_time = 1  # Start with 1 second backoff

    while attempt < max_attempts:
        attempt += 1
        try:
            message = client.messages.create(body=body, from_=from_number, to=to)
            logger.info(f"SMS sent successfully to {to}, SID: {message.sid}")
            return message.sid

        except TwilioRestException as e:
            status_code = getattr(e, "status", 0)

            # Check if error is transient (5xx or 429 Too Many Requests)
            is_retryable = status_code >= 500 or status_code == 429

            if is_retryable and attempt < max_attempts:
                logger.warning(
                    f"Transient Twilio error: {str(e)}. "
                    f"Retry {attempt}/{max_attempts} in {backoff_time}s"
                )
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                continue

            # Not retryable or max attempts reached
            logger.error(f"Failed to send SMS: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send SMS: {str(e)}",
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send SMS: {str(e)}",
            ) from e


async def send_fax(
    to: str, media_url: str, from_number: Optional[str] = None, max_attempts: int = 3
) -> str:
    """Sends fax via Twilio Programmable Fax with retry logic.

    Args:
        to: Recipient fax number in E.164 format (e.g. +15551234567)
        media_url: URL to the document to fax (must be publicly accessible)
        from_number: Sender fax number (defaults to TWILIO_FAX_FROM)
        max_attempts: Maximum number of retry attempts for transient errors

    Returns:
        Twilio fax SID

    Raises:
        ValueError: If Twilio configuration is missing
        HTTPException: If fax sending fails after retries
    """
    if not from_number:
        from_number = settings.TWILIO_FAX_FROM

    if not from_number:
        logger.error("TWILIO_FAX_FROM not configured")
        raise ValueError("Twilio fax sender number not configured")

    client = get_twilio_client()
    attempt = 0
    backoff_time = 1  # Start with 1 second backoff

    while attempt < max_attempts:
        attempt += 1
        try:
            fax = client.fax.v1.faxes.create(
                from_=from_number, to=to, media_url=media_url
            )
            logger.info(f"Fax sent successfully to {to}, SID: {fax.sid}")
            return fax.sid

        except TwilioRestException as e:
            status_code = getattr(e, "status", 0)

            # Check if error is transient (5xx or 429 Too Many Requests)
            is_retryable = status_code >= 500 or status_code == 429

            if is_retryable and attempt < max_attempts:
                logger.warning(
                    f"Transient Twilio error: {str(e)}. "
                    f"Retry {attempt}/{max_attempts} in {backoff_time}s"
                )
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
                continue

            # Not retryable or max attempts reached
            logger.error(f"Failed to send fax: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send fax: {str(e)}",
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error sending fax: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send fax: {str(e)}",
            ) from e
