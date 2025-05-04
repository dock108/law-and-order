"""Pydantic schemas for the PI Automation API.

This module contains Pydantic models for request and response schemas.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, HttpUrl


class ClientIn(BaseModel):
    """Schema for client data in an intake request."""

    full_name: str
    dob: date
    phone: str
    email: EmailStr
    address: str


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
    """Schema for the intake response."""

    client_id: int
    incident_id: int
