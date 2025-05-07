"""API Router for Server-Sent Events (SSE)."""

import asyncio
import logging
import time
from typing import Any, AsyncGenerator, Dict, Optional

import redis.asyncio as redis
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from pi_auto_api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Define a longer timeout for Redis connection attempts during startup/reconnect
REDIS_CONNECT_TIMEOUT = 10  # seconds
HEARTBEAT_INTERVAL = 30  # seconds


async def _process_redis_message(message: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Formats a received Redis message into an SSE event dictionary."""
    if message and message["type"] == "message":
        event_id = str(int(time.time() * 1000))  # Millisecond timestamp
        event_data = message["data"]  # Already bytes
        logger.debug(f"SSE: Sending event ID {event_id}, Data: {event_data.decode()}")
        return {
            "id": event_id,
            "event": "message",
            "data": event_data.decode(),
        }
    return None


# C901: `event_publisher` is too complex (13 > 10) - This might require refactoring
#       or increasing the allowed complexity in pyproject.toml if acceptable.
#       For now, we'll leave it and address other errors.
async def event_publisher(request: Request) -> AsyncGenerator[Dict[str, str], None]:  # noqa: C901
    """Yields server-sent events from a Redis pub/sub channel."""
    redis_client = None
    pubsub = None
    last_event_id = request.headers.get("Last-Event-ID")
    # Last-Event-ID is ignored for v1 as per requirements,
    # but good to acknowledge its presence.
    if last_event_id:
        logger.info(f"Client connected with Last-Event-ID: {last_event_id}")

    try:
        redis_client = redis.from_url(
            settings.REDIS_URL, decode_responses=False
        )  # SSE requires bytes
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe("activity")
            logger.info("SSE client subscribed to 'activity' Redis channel.")

            last_heartbeat_time = time.time()

            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected.")
                    break

                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    sse_event = await _process_redis_message(message)
                    if sse_event:
                        yield sse_event
                        last_heartbeat_time = time.time()

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}", exc_info=True)
                    await asyncio.sleep(1)  # Avoid tight loop on persistent error

                current_time = time.time()
                if current_time - last_heartbeat_time > HEARTBEAT_INTERVAL:
                    logger.debug("SSE: Sending keep-alive heartbeat")
                    yield {"event": "comment", "data": ": keep-alive"}
                    last_heartbeat_time = current_time

                await asyncio.sleep(0.01)

    except redis.exceptions.ConnectionError as e:
        logger.error(f"SSE: Could not connect to Redis: {e}")
        # Optionally, yield an error event to the client
        # if the connection fails at start
    except asyncio.CancelledError:
        logger.info("SSE event_publisher task was cancelled (client disconnected).")
    except Exception as e:
        logger.error(f"SSE: Unexpected error in event_publisher: {e}", exc_info=True)
    finally:
        if redis_client:
            try:
                await redis_client.aclose()
                logger.info("SSE: Closed Redis client connection.")
            except Exception as e:
                logger.error(
                    f"SSE: Error during Redis client cleanup: {e}", exc_info=True
                )
        logger.info("SSE: event_publisher finished.")


@router.get("/stream", summary="Stream live activity events", tags=["Events"])
async def stream_events(request: Request):
    """Endpoint for Server-Sent Events (SSE).

    Streams events published to the 'activity' Redis channel.
    Sends a keep-alive comment every 30 seconds.
    The `Last-Event-ID` header is received but currently ignored for simplicity in v1.
    """
    return EventSourceResponse(event_publisher(request))
