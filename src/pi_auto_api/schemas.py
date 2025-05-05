"""Pydantic schemas for the PI Automation API.

This module contains Pydantic models for request and response schemas.
"""

import re
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class ClientIn(BaseModel):
    """Schema for client data in an intake request."""

    full_name: str
    dob: date
    phone: str = Field(
        description="Client phone number in format: XXX-XXX-XXXX or (XXX) XXX-XXXX"
    )
    email: EmailStr
    address: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Check for North American phone number formats:
        # XXX-XXX-XXXX, (XXX) XXX-XXXX, XXX.XXX.XXXX, etc.
        pattern = r"^(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?(\d{3})[-.\s]?(\d{4})$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid phone number format. "
                "Expected format like: 555-123-4567 or (555) 123-4567"
            )
        return v


class IncidentIn(BaseModel):
    """Schema for incident data in an intake request."""

    date: date
    location: str
    police_report_url: Optional[HttpUrl] = None
    injuries: List[str] = []
    vehicle_damage_text: Optional[str] = None


class IntakePayload(BaseModel):
    """Schema for the complete intake request payload."""

    client: ClientIn
    incident: IncidentIn


class ClientOut(BaseModel):
    """Schema for client data in responses."""

    id: int
    full_name: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class IncidentOut(BaseModel):
    """Schema for incident data in responses."""

    id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class IntakeResponse(BaseModel):
    """Response model for client intake."""

    client_id: int
    incident_id: int
    status: str = "processing"


# DocuSign webhook models
class DocuSignCustomField(BaseModel):
    """Model for DocuSign envelope custom fields."""

    name: str
    value: str


class DocuSignWebhookPayload(BaseModel):
    """Model for DocuSign Connect webhook payload.

    This is a simplified version of the actual payload,
    containing only the fields we need for our application.
    """

    envelopeId: str
    status: str
    emailSubject: str = "Retainer Agreement"
    customFields: Optional[List[DocuSignCustomField]] = None

    class Config:
        """Pydantic config."""

        # Allow extra fields in the payload that we don't need
        extra = "allow"
