"""Main FastAPI application.

This module contains the FastAPI application instance and route definitions.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Optional

import asyncpg
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pi_auto_api.config import settings
from pi_auto_api.db import create_intake
from pi_auto_api.schemas import (
    DocuSignWebhookPayload,
    FinalizeSettlementPayload,
    IntakePayload,
    IntakeResponse,
)
from pi_auto_api.tasks.disbursement import generate_disbursement_sheet
from pi_auto_api.tasks.insurance_notice import send_insurance_notice
from pi_auto_api.tasks.retainer import generate_retainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global database connection pool
db_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.

    This function is called when the application starts and stops.
    It can be used to initialize and clean up resources.

    Args:
        app: The FastAPI application instance.
    """
    # Startup: Validate required settings
    missing_settings = []
    if not settings.SUPABASE_URL:
        missing_settings.append("SUPABASE_URL")
        logger.warning("SUPABASE_URL is not set. The /readyz endpoint will fail.")

    if not settings.SUPABASE_KEY:
        missing_settings.append("SUPABASE_KEY")
        logger.warning("SUPABASE_KEY is not set.")

    if missing_settings:
        logger.warning(
            f"Missing required settings: {', '.join(missing_settings)}. "
            "Set these in .env file or environment variables."
        )

    logger.info("Starting up PI Auto API")

    # Initialize the database connection pool if URL is configured
    global db_pool
    if settings.SUPABASE_URL:
        try:
            db_pool = await asyncpg.create_pool(
                settings.SUPABASE_URL,
                min_size=2,
                max_size=10,
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {str(e)}")
            db_pool = None

    yield

    # Shutdown: Close the connection pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")

    logger.info("Shutting down PI Auto API")


# Create the FastAPI application
app = FastAPI(
    title="PI Automation API",
    version="0.1.0",
    description="API for automating personal injury case management workflows",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Add X-Request-ID header to requests and responses.

    Args:
        request: The incoming request.
        call_next: The next middleware or route handler.

    Returns:
        The response from the next middleware or route handler.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Add request ID to the logger context
    logger.info(f"Processing request {request_id}: {request.method} {request.url.path}")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Health check route
@app.get("/healthz", summary="Health check endpoint")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint.

    Returns:
        Dictionary with status "ok".
    """
    return {"status": "ok"}


# Database health check dependency
async def check_database() -> None:
    """Check if the database is available.

    Raises:
        HTTPException: If the database is not available.
    """
    global db_pool

    # Create the pool if it doesn't exist yet
    if not db_pool and settings.SUPABASE_URL:
        try:
            db_pool = await asyncpg.create_pool(
                settings.SUPABASE_URL,
                min_size=2,
                max_size=10,
            )
            logger.info("Database connection pool initialized during health check")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection failed: {str(e)}",
            ) from e

    if not db_pool:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool not available",
        )

    try:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
            logger.info("Database check successful")
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {str(e)}",
        ) from e


# Docassemble health check dependency
async def check_docassemble() -> None:
    """Check if the Docassemble API is available.

    Raises:
        HTTPException: If the Docassemble API is not available.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.DOCASSEMBLE_URL}/health")
            if response.status_code != 200:
                logger.error(f"Docassemble API check failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Docassemble API not available: {response.text}",
                )
            logger.info("Docassemble API check successful")
    except Exception as e:
        logger.error(f"Docassemble API check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Docassemble API not available: {str(e)}",
        ) from e


# Readiness check route using dependencies
@app.get("/readyz", summary="Readiness check endpoint")
async def readiness_check(
    db: None = Depends(check_database),
    docassemble: None = Depends(check_docassemble),
) -> Dict[str, str]:
    """Check if the application is ready to serve requests.

    This endpoint checks if the database and Docassemble API are available.

    Args:
        db: Result of database check dependency.
        docassemble: Result of Docassemble API check dependency.

    Returns:
        Dictionary with status "ok" if all systems are ready.
    """
    return {"status": "ok"}


# Add API root endpoint to redirect to docs
@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Redirect to API documentation.

    Returns:
        Redirects to the /docs endpoint.
    """
    return JSONResponse(
        content={
            "message": "PI Automation API",
            "documentation": "/docs",
            "health": "/healthz",
            "readiness": "/readyz",
            "intake": "/intake",
        }
    )


# Client intake endpoint
@app.post(
    "/intake",
    response_model=IntakeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create new client intake",
)
async def intake(payload: IntakePayload) -> IntakeResponse:
    """Create a new client intake record.

    This endpoint creates a new client and incident record in the database,
    and queues a task to generate a retainer agreement.

    Args:
        payload: The intake payload containing client and incident data

    Returns:
        A response containing the created client_id and incident_id

    Raises:
        HTTPException: If there's an error creating the records
    """
    try:
        # Create the intake records
        result = await create_intake(payload)

        # Queue the retainer generation task
        generate_retainer.delay(result["client_id"])

        return IntakeResponse(
            client_id=result["client_id"],
            incident_id=result["incident_id"],
        )
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error in intake: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        # Handle database errors
        logger.error(f"Error creating intake: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create intake. Please try again later.",
        ) from e


# Settlement finalization endpoint
@app.post(
    "/internal/finalize_settlement",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Finalize settlement and generate disbursement sheet",
)
async def finalize_settlement(
    payload: FinalizeSettlementPayload,
    request: Request,
    # Uncomment for production with auth
    # user: str = Depends(get_current_user),
    # Only allow lawyers and paralegals
    # role: str = Depends(verify_role(["lawyer", "paralegal"])),
) -> Dict[str, Any]:
    """Finalize a settlement and generate a disbursement sheet.

    This endpoint updates settlement details for an incident and queues
    a task to generate and send a disbursement sheet for signature.

    Args:
        payload: The settlement details including incident_id, settlement_amount,
                lien_total, and adjustments.
        request: The request object.

    Returns:
        Status information and task ID.

    Raises:
        HTTPException: If there's an error updating the settlement details.
    """
    try:
        conn = None
        try:
            # Connect to the database
            conn = await asyncpg.connect(settings.SUPABASE_URL)

            # 1. Update incident with settlement details
            update_query = """
            UPDATE incident
            SET settlement_amount = $1,
                lien_total = $2
            WHERE id = $3
            RETURNING id
            """
            incident_id = await conn.fetchval(
                update_query,
                payload.settlement_amount,
                payload.lien_total,
                payload.incident_id,
            )

            if not incident_id:
                raise ValueError(f"Incident {payload.incident_id} not found")

            # 2. Insert fee adjustments if any
            if payload.adjustments:
                for adjustment in payload.adjustments:
                    insert_query = """
                    INSERT INTO fee_adjustments (incident_id, description, amount)
                    VALUES ($1, $2, $3)
                    """
                    await conn.execute(
                        insert_query,
                        payload.incident_id,
                        adjustment.description,
                        adjustment.amount,
                    )

            logger.info(f"Settlement finalized for incident {payload.incident_id}")

        finally:
            if conn:
                await conn.close()

        # 3. Queue task to generate disbursement sheet
        task = generate_disbursement_sheet.delay(payload.incident_id)
        logger.info(
            f"Queued disbursement sheet task {task.id} "
            f"for incident {payload.incident_id}"
        )

        return {
            "status": "success",
            "message": "Settlement finalized and disbursement sheet generation queued",
            "incident_id": payload.incident_id,
            "task_id": task.id,
        }

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error in settlement finalization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        # Handle database errors
        logger.error(f"Error finalizing settlement: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize settlement. Please try again later.",
        ) from e


@app.post(
    "/webhooks/docusign",
    status_code=status.HTTP_200_OK,
    summary="DocuSign Connect webhook endpoint",
)
async def docusign_webhook(payload: DocuSignWebhookPayload) -> Dict[str, str]:
    """Process DocuSign webhook for completed envelopes.

    This endpoint receives notifications from DocuSign when a document
    has been signed. When a retainer agreement is signed, it triggers
    the insurance notice flow to send LORs to insurance carriers.

    Args:
        payload: The DocuSign webhook payload

    Returns:
        Acknowledgment of receipt
    """
    logger.info(f"Received DocuSign webhook: envelope_id={payload.envelopeId}")

    # Check if this is a completed envelope event
    if payload.status != "completed":
        logger.info(f"Ignoring non-completed envelope: status={payload.status}")
        return {"status": "ignored", "reason": "not_completed"}

    # In a real implementation, you would verify that this envelope
    # is for a retainer agreement by checking against a database record.
    # For now, we'll assume it's a retainer and extract the client_id
    # from custom fields or the subject line.

    # Extract client_id from payload (in real implementation, this could be a
    # custom field in the DocuSign envelope or retrieved from database)
    try:
        # This is a simplified example; in production you would query DB
        # to match the envelope_id to your client records
        if hasattr(payload, "customFields") and payload.customFields:
            # Try to find client_id from custom fields
            for field in payload.customFields:
                if field.name == "client_id":
                    client_id = int(field.value)
                    break
            else:
                # For demo purposes, extract a numeric ID from email subject
                # This would be replaced with proper DB lookup in production
                client_id = int(payload.emailSubject.split("ID:")[-1].strip())
        else:
            # Fallback for testing - assume a default ID
            # In production, this would be a DB lookup
            client_id = 101

        logger.info(f"Extracted client_id: {client_id}")

        # Queue the insurance notice task
        send_insurance_notice.delay(client_id)
        logger.info(f"Queued insurance notice task for client_id: {client_id}")

        return {"status": "success", "client_id": str(client_id)}
    except Exception as e:
        logger.error(f"Error processing DocuSign webhook: {str(e)}", exc_info=True)
        # We still return 200 to DocuSign to acknowledge receipt,
        # but include error details in the response
        return {"status": "error", "reason": str(e)}
