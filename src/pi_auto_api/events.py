"""Helper functions for publishing events to Redis pub/sub."""

import json

import redis.asyncio as redis

from pi_auto_api.config import settings

# Initialize Redis client globally or manage its lifecycle appropriately
# For simplicity in this module, we'll create it here.
# In a larger app, you might manage this with FastAPI lifespan events.
_redis_instance = None


async def get_redis_client():
    """Get a Redis client instance, creating it if necessary."""
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_instance


async def record_event(event: dict):
    """Publish a JSON event to the 'activity' Redis channel.

    Args:
        event: A dictionary representing the event to publish.
               It will be serialized to JSON.
    """
    redis_client = await get_redis_client()
    await redis_client.publish("activity", json.dumps(event))


async def close_redis_client():
    """Close the Redis client connection if it was initialized."""
    global _redis_instance
    if _redis_instance:
        await _redis_instance.aclose()
        _redis_instance = None
