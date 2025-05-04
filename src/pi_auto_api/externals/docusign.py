"""Client for interacting with the DocuSign eSignature API."""

import base64
import logging
from datetime import datetime, timedelta

from docusign_esign import (
    ApiClient,
    ApiException,
    Document,
    EnvelopeDefinition,
    EnvelopesApi,
    Recipients,
    Signer,
    SignHere,
    Tabs,
)
from fastapi import HTTPException, status

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)

# Cache for DocuSign API client with JWT auth
_api_client_cache = None
_token_expiry = None


def _read_private_key(path: str) -> str:
    """Read private key from file.

    Args:
        path: Path to the private key file.

    Returns:
        Contents of the private key file.

    Raises:
        FileNotFoundError: If the private key file doesn't exist.
        IOError: For other errors reading the private key.
    """
    try:
        with open(path, "r") as key_file:
            return key_file.read()
    except FileNotFoundError:
        # Use from None to indicate this is a deliberate re-raise with new message
        raise FileNotFoundError(f"DocuSign private key not found at: {path}") from None
    except Exception as e:
        raise IOError(f"Error reading DocuSign private key: {e}") from e


def _get_docusign_api_client() -> ApiClient:
    """Configure and return a DocuSign API client with JWT authentication.

    Returns a cached client if one exists and the token is not expired.
    Otherwise, creates a new client with a fresh JWT token.
    """
    global _api_client_cache, _token_expiry

    # Check if we have a cached client with a valid token
    current_time = datetime.now()
    if _api_client_cache and _token_expiry and current_time < _token_expiry:
        logger.debug("Using cached DocuSign JWT token")
        return _api_client_cache

    logger.debug("Generating new DocuSign JWT token")

    # Create new API client
    api_client = ApiClient()
    api_client.host = settings.DOCUSIGN_BASE_URL

    if not all(
        [
            settings.DOCUSIGN_ACCOUNT_ID,
            settings.DOCUSIGN_INTEGRATOR_KEY,
            settings.DOCUSIGN_USER_ID,
            settings.DOCUSIGN_PRIVATE_KEY,
        ]
    ):
        raise ValueError("Missing required DocuSign configuration settings.")

    # First check if the private key file exists before attempting JWT auth
    if not settings.DOCUSIGN_PRIVATE_KEY:
        logger.warning("DOCUSIGN_PRIVATE_KEY setting is empty")
        raise ValueError("DocuSign private key path is not configured")

    try:
        # The _read_private_key function already handles its own exceptions
        private_key = _read_private_key(settings.DOCUSIGN_PRIVATE_KEY)
    except FileNotFoundError:
        # Log a warning but re-raise the exception
        logger.warning(
            f"DocuSign private key not found at configured path: "
            f"{settings.DOCUSIGN_PRIVATE_KEY}"
        )
        raise

    # Set token expiry to slightly less than the actual expiry time (3600 seconds)
    token_lifetime = 3600  # seconds
    buffer = 300  # 5 minutes buffer to avoid edge cases

    # Request JWT token
    try:
        api_client.configure_jwt_authorization_flow(
            private_key=private_key,
            client_id=settings.DOCUSIGN_INTEGRATOR_KEY,
            user_id=settings.DOCUSIGN_USER_ID,
            scopes=["signature", "impersonation"],
            expires_in=token_lifetime,
        )

        # Update the cache and expiry time
        _api_client_cache = api_client
        _token_expiry = current_time + timedelta(seconds=token_lifetime - buffer)

        return api_client
    except ApiException as e:
        # Safely log the exception details
        error_details = f"status={e.status}, reason={e.reason}"
        if hasattr(e, "body") and e.body:
            # Log truncated body
            error_details += f", body={e.body[:100]}..."
        logger.error(
            f"DocuSign JWT authentication failed: {error_details}", exc_info=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # Use reason in detail
            detail=f"DocuSign authentication error: {e.reason}",
        ) from e


async def send_envelope(pdf_bytes: bytes, client_email: str, client_name: str) -> str:
    """Create and send a DocuSign envelope for signature.

    Args:
        pdf_bytes: The raw PDF document bytes.
        client_email: The email address of the client signer.
        client_name: The full name of the client signer.

    Returns:
        The ID of the created DocuSign envelope.

    Raises:
        HTTPException: If the DocuSign API call fails.
    """
    api_client = _get_docusign_api_client()
    envelopes_api = EnvelopesApi(api_client)

    # Create the document object
    document = Document(
        document_base64=base64.b64encode(pdf_bytes).decode("ascii"),
        name="Retainer Agreement",
        file_extension="pdf",
        document_id="1",
    )

    # Create the signer recipient object
    signer = Signer(
        email=client_email,
        name=client_name,
        recipient_id="1",
        routing_order="1",
        # Specify tabs for the signer (where they need to sign)
        tabs=Tabs(
            sign_here_tabs=[
                SignHere(
                    document_id="1", page_number="1", x_position="100", y_position="100"
                )
            ]
        ),
    )

    # Create the envelope definition
    envelope_definition = EnvelopeDefinition(
        email_subject="Please Sign: Retainer Agreement",
        documents=[document],
        recipients=Recipients(signers=[signer]),
        status="sent",  # Send the envelope immediately
    )

    try:
        results = await api_client.loop.run_in_executor(
            None,  # Use default executor (ThreadPoolExecutor)
            lambda: envelopes_api.create_envelope(
                account_id=settings.DOCUSIGN_ACCOUNT_ID,
                envelope_definition=envelope_definition,
            ),
        )
        envelope_id = results.envelope_id
        logger.info(f"Successfully sent DocuSign envelope: {envelope_id}")
        return envelope_id
    except ApiException as e:
        # Safely log the exception details
        error_details = f"status={e.status}, reason={e.reason}"
        if hasattr(e, "body") and e.body:
            error_details += f", body={e.body[:100]}..."  # Log truncated body
        logger.error(
            f"DocuSign API error creating envelope: {error_details}", exc_info=False
        )
        # Use reason and truncated body in the detail for better debugging
        detail = f"DocuSign API error: {e.reason}"
        if hasattr(e, "body") and e.body:
            detail += f" - {e.body[:100]}..."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e
