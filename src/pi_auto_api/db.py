"""Database operations for the PI Automation API.

This module contains helpers for database operations.
"""

import json
import logging
from datetime import datetime
from typing import Dict

import asyncpg

from pi_auto_api.config import settings
from pi_auto_api.schemas import IntakePayload

logger = logging.getLogger(__name__)


async def create_intake(payload: IntakePayload) -> Dict[str, int]:
    """Create a new client and incident record in the database.

    Args:
        payload: The intake payload containing client and incident data

    Returns:
        Dict containing the created client_id and incident_id

    Raises:
        Exception: If there's an error creating the records
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    conn = None
    try:
        # Connect to the database
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Start a transaction to ensure both inserts succeed or both fail
        async with conn.transaction():
            # Insert client record
            client_query = """
            INSERT INTO client (full_name, dob, phone, email, address)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """
            client_id = await conn.fetchval(
                client_query,
                payload.client.full_name,
                payload.client.dob,
                payload.client.phone,
                payload.client.email,
                payload.client.address,
            )

            # Insert incident record
            incident_query = """
            INSERT INTO incident (
                client_id, date, location, police_report_url,
                injuries, vehicle_damage_text
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """
            incident_id = await conn.fetchval(
                incident_query,
                client_id,
                payload.incident.date,
                payload.incident.location,
                (
                    str(payload.incident.police_report_url)
                    if payload.incident.police_report_url
                    else None
                ),
                json.dumps(payload.incident.injuries),
                payload.incident.vehicle_damage_text,
            )

            # Return the IDs
            return {
                "client_id": client_id,
                "incident_id": incident_id,
            }
    except Exception as e:
        logger.error(f"Error creating intake: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            await conn.close()


async def get_client_payload(client_id: int) -> dict:
    """Fetch client and incident data shaped for Docassemble retainer interview.

    Args:
        client_id: The ID of the client.

    Returns:
        A dictionary containing client and incident data.

    Raises:
        ValueError: If the client or incident is not found.
        Exception: If there is a database error.
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Use a transaction for consistent read
        async with conn.transaction():
            query = """
            SELECT
                c.full_name, c.dob, c.phone, c.email, c.address,
                i.date AS incident_date, i.location AS incident_location,
                i.injuries AS incident_injuries,
                i.vehicle_damage_text AS incident_vehicle_damage_text
            FROM client c
            JOIN incident i ON c.id = i.client_id
            WHERE c.id = $1;
            """
            record = await conn.fetchrow(query, client_id)

            if not record:
                raise ValueError(f"Client with ID {client_id} not found.")

            # Shape the data for Docassemble
            payload = {
                "client": {
                    "full_name": record["full_name"],
                    "dob": str(record["dob"]),  # Convert date to string
                    "phone": record["phone"],
                    "email": record["email"],
                    "address": record["address"],
                },
                "incident": {
                    "date": str(record["incident_date"]),  # Convert date to string
                    "location": record["incident_location"],
                    # Injuries are stored as JSON string, need to load them
                    "injuries": json.loads(record["incident_injuries"]),
                    "vehicle_damage_text": record["incident_vehicle_damage_text"],
                },
            }
            return payload
    except Exception as e:
        logger.error(f"Error fetching client data: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            await conn.close()


async def get_insurance_payload(client_id: int) -> dict:
    """Fetch client, incident, and insurance data for Letter of Representation.

    Args:
        client_id: The ID of the client.

    Returns:
        A dictionary containing client, incident, and insurance data formatted
        for use with the letter of representation template.

    Raises:
        ValueError: If the client, incident, or insurance data is not found.
        Exception: If there is a database error.
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # First, get the client and incident data
        client_query = """
        SELECT
            c.id AS client_id,
            c.full_name,
            c.dob,
            c.phone,
            c.email,
            c.address,
            i.id AS incident_id,
            i.date AS incident_date,
            i.location AS incident_location
        FROM client c
        JOIN incident i ON c.id = i.client_id
        WHERE c.id = $1;
        """
        client_record = await conn.fetchrow(client_query, client_id)

        if not client_record:
            raise ValueError(f"Client with ID {client_id} not found.")

        incident_id = client_record["incident_id"]

        # Now fetch insurance information
        insurance_query = """
        SELECT
            id,
            carrier_name,
            policy_number,
            claim_number,
            is_client_side
        FROM insurance
        WHERE incident_id = $1;
        """
        insurance_records = await conn.fetch(insurance_query, incident_id)

        if not insurance_records:
            logger.warning(f"No insurance records found for incident {incident_id}")

        # Format the data for the template
        client_data = {
            "full_name": client_record["full_name"],
            "dob": str(client_record["dob"]) if client_record["dob"] else None,
            "phone": client_record["phone"],
            "email": client_record["email"],
            "address": client_record["address"],
        }

        incident_data = {
            "date": (
                str(client_record["incident_date"])
                if client_record["incident_date"]
                else None
            ),
            "location": client_record["incident_location"],
        }

        # Format insurance data, separating client and adverse carriers
        client_insurance = {}
        adverse_insurance = []

        for record in insurance_records:
            insurance_data = {
                "carrier_name": record["carrier_name"],
                "policy_number": record["policy_number"],
                "claim_number": record["claim_number"],
            }

            if record["is_client_side"]:
                client_insurance = insurance_data
            else:
                adverse_insurance.append(insurance_data)

        # Build the complete payload
        payload = {
            "client": client_data,
            "incident": incident_data,
            "client_insurance": client_insurance,
            "adverse_insurance": adverse_insurance,
            # Add standard firm/attorney details that would be used on letterhead
            "firm": {
                "name": "PI Auto Law Firm",
                "address": "123 Legal Avenue",
                "city": "Lawtown",
                "state": "NY",
                "zip": "10001",
                "phone": "(555) 123-4567",
                "fax": "(555) 123-4568",
                "email": "contact@piautolaw.com",
            },
            "attorney": {
                "full_name": "Jane Smith",
                "title": "Senior Attorney",
                "bar_number": "NY123456",
            },
        }

        return payload

    except Exception as e:
        logger.error(f"Error fetching insurance data: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure connection is closed even if an exception occurs
        if conn:
            await conn.close()


async def get_provider_payload(incident_id: int, provider_id: int) -> dict:
    """Fetch client, incident, and provider data for medical records request.

    Args:
        incident_id: The ID of the incident
        provider_id: The ID of the healthcare provider

    Returns:
        A dictionary containing client, incident, and provider data formatted for
        use with Docassemble medical records request template

    Raises:
        ValueError: If the client, incident, or provider data is not found
        Exception: If there is a database error
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")

    conn = None
    try:
        conn = await asyncpg.connect(settings.SUPABASE_URL)

        # Fetch client, incident, and provider data in a single query
        query = """
        SELECT
            c.id AS client_id,
            c.full_name AS client_name,
            c.dob AS client_dob,
            c.phone AS client_phone,
            c.email AS client_email,
            c.address AS client_address,
            i.id AS incident_id,
            i.date AS incident_date,
            i.location AS incident_location,
            i.injuries AS incident_injuries,
            p.id AS provider_id,
            p.name AS provider_name,
            p.address AS provider_address,
            p.phone AS provider_phone,
            p.fax AS provider_fax,
            p.specialty AS provider_specialty
        FROM client c
        JOIN incident i ON c.id = i.client_id
        JOIN provider p ON p.id = $2
        WHERE i.id = $1
        """

        record = await conn.fetchrow(query, incident_id, provider_id)

        if not record:
            raise ValueError(
                f"No data found for incident ID {incident_id} "
                f"and provider ID {provider_id}"
            )

        # Shape the data for Docassemble
        payload = {
            "client": {
                "id": record["client_id"],
                "full_name": record["client_name"],
                "dob": str(record["client_dob"]),
                "phone": record["client_phone"],
                "email": record["client_email"],
                "address": record["client_address"],
            },
            "incident": {
                "id": record["incident_id"],
                "date": str(record["incident_date"]),
                "location": record["incident_location"],
                "injuries": json.loads(record["incident_injuries"]),
            },
            "provider": {
                "id": record["provider_id"],
                "name": record["provider_name"],
                "address": record["provider_address"],
                "phone": record["provider_phone"],
                "fax": record["provider_fax"],
                "specialty": record["provider_specialty"],
            },
            "letter_date": datetime.now().strftime("%B %d, %Y"),
            "law_firm": {
                "name": "Law & Order Legal Services",
                "address": "123 Legal Street, New York, NY 10001",
                "phone": "(212) 555-1212",
                "fax": "(212) 555-1213",
                "email": "contact@lawandorder.legal",
            },
        }

        return payload
    except Exception as e:
        logger.error(f"Error fetching provider data: {str(e)}", exc_info=True)
        raise
    finally:
        if conn:
            await conn.close()
