"""Celery task discovery and package initialization."""

# Import the Celery application instance first
from pi_auto_api.celery_app import app

# Import task modules to ensure tasks are registered with Celery
from . import (
    billing,
    damages,
    demand,
    disbursement,
    insurance_notice,
    medical_records,
    retainer,
)

__all__ = (
    "app",  # Expose app for potential direct use (e.g., by tests)
    "billing",
    "damages",
    "demand",
    "disbursement",
    "insurance_notice",
    "medical_records",
    "retainer",
)
