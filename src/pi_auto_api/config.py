"""Configuration settings for the PI Automation API.

This module uses pydantic-settings to manage environment variables and
configuration settings for the API.
"""

import logging
import os
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        DATABASE_URL: Connection URL for SQLAlchemy async
        SUPABASE_URL: URL of the Supabase instance
        SUPABASE_KEY: API key for Supabase
        DOCASSEMBLE_URL: URL of the Docassemble API
        ALLOWED_ORIGINS: List of allowed origins for CORS
        REDIS_URL: Connection URL for Redis
        DOCUSIGN_BASE_URL: DocuSign API base URL
        DOCUSIGN_ACCOUNT_ID: DocuSign Account ID
        DOCUSIGN_INTEGRATOR_KEY: DocuSign Integrator Key (Client ID)
        DOCUSIGN_USER_ID: DocuSign User ID (GUID)
        DOCUSIGN_PRIVATE_KEY: Path to the DocuSign private key file
        SENDGRID_API_KEY: API key for SendGrid
        TWILIO_ACCOUNT_SID: Twilio Account SID
        TWILIO_AUTH_TOKEN: Twilio Auth Token
        TWILIO_SMS_FROM: Phone number to send SMS from
        TWILIO_FAX_FROM: Phone number to send faxes from
        JWT_SECRET: Secret key for JWT
        JWT_EXP_MINUTES: Expiration time for JWT in minutes
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # General settings
    # ... (other settings)

    # Database settings
    DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/pi_auto_db"  # Default DB
    )
    SUPABASE_URL: Optional[str] = None  # For asyncpg pool if still used separately
    SUPABASE_KEY: Optional[str] = None

    # Docassemble settings
    DOCASSEMBLE_URL: str = "http://localhost:5000"  # Default to local dev server

    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000"  # Default to allow frontend dev

    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"  # Default to Redis container

    # DocuSign settings
    DOCUSIGN_BASE_URL: str = "https://demo.docusign.net/restapi"
    DOCUSIGN_ACCOUNT_ID: Optional[str] = None
    DOCUSIGN_INTEGRATOR_KEY: Optional[str] = None
    DOCUSIGN_USER_ID: Optional[str] = None
    DOCUSIGN_PRIVATE_KEY: str = "./docusign_private.key"  # Default to local file

    # SendGrid settings
    SENDGRID_API_KEY: Optional[str] = None

    # Twilio settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_SMS_FROM: Optional[str] = None
    TWILIO_FAX_FROM: Optional[str] = None

    # JWT settings for Staff Authentication
    JWT_SECRET: Optional[str] = None
    JWT_EXP_MINUTES: int = 60

    @field_validator("DOCUSIGN_PRIVATE_KEY")
    @classmethod
    def validate_docusign_key_path(cls, v: str) -> str:
        """Verify that the private key path is valid.

        This validator logs a warning if the file doesn't exist but doesn't
        raise an error since the app might need to start without DocuSign.
        """
        if v and not os.path.isfile(v):
            logger.warning(
                f"DocuSign private key file not found at '{v}'. "
                "DocuSign functionality will be unavailable."
            )
        return v

    @field_validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Convert comma-separated string of origins into a list.

        Args:
            v: Comma-separated string of origins

        Returns:
            List of origins
        """
        if isinstance(v, str):
            # Handle the special case "*"
            if v == "*":
                return ["*"]
            # Split comma-separated string
            return [origin.strip() for origin in v.split(",") if origin]
        # If it's already a list (e.g., from a non-env source), return as is
        elif isinstance(v, list):
            return v
        # Raise error for unexpected types
        raise ValueError("ALLOWED_ORIGINS must be a comma-separated string or a list")


# Create a global settings instance
settings = Settings()

# Celery Configuration - mapped from the Settings instance
# These need to be top-level attributes in this module for Celery to pick them up
# when using app.config_from_object("pi_auto_api.config")

broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True
# Optional: Define task_routes if you have specific routing needs
# task_routes = {
#     'pi_auto_api.tasks.some_task': {'queue': 'special_queue'},
# }

# Optional: Add beat_schedule here if you prefer it over celery_app.py
# beat_schedule = {
#     "nightly-medical-record-request": {
#         "task": "send_medical_record_requests", # Ensure task name matches definition
#         "schedule": crontab(hour=2, minute=0),
#     },
#     "nightly-demand-package-check": {
#         "task": "check_and_build_demand", # Ensure task name matches definition
#         "schedule": crontab(hour=3, minute=0),
#     },
# }
