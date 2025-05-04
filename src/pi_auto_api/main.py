"""Main FastAPI application.

This module contains the FastAPI application instance and route definitions.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Callable, Dict, Optional

import asyncpg
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pi_auto_api.config import settings
from pi_auto_api.db import create_intake
from pi_auto_api.schemas import IntakePayload, IntakeResponse
from pi_auto_api.tasks import generate_retainer

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
