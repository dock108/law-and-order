"""Configuration settings for the PI Automation API.

This module uses pydantic-settings to manage environment variables and
configuration settings for the API.
"""

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
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
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Database settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # Docassemble settings
    DOCASSEMBLE_URL: str = "http://localhost:5000"  # Default to local dev server

    # CORS settings
    ALLOWED_ORIGINS: str = "*"  # Default to allow all origins in dev

    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"  # Default to Redis container

    # DocuSign settings
    DOCUSIGN_BASE_URL: str = "https://demo.docusign.net/restapi"
    DOCUSIGN_ACCOUNT_ID: Optional[str] = None
    DOCUSIGN_INTEGRATOR_KEY: Optional[str] = None
    DOCUSIGN_USER_ID: Optional[str] = None
    DOCUSIGN_PRIVATE_KEY: str = "docusign_private.key"  # Default path

    @field_validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Convert comma-separated string of origins into a list.

        Args:
            v: Comma-separated string of origins

        Returns:
            List of origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin]
        if isinstance(v, str) and v == "*":
            return ["*"]
        return v


# Create a global settings instance
settings = Settings()
