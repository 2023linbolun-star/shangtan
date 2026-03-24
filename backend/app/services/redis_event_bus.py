"""
Redis-backed event bus for cross-process event delivery.
Replaces the in-process EventBus for v2.0 autonomous operations.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import REDIS_URL

logger = logging.getLogger("shangtanai.events")


class RedisEventBus:
    def __init__(self, redis_url: str = REDIS_URL):
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def emit(self, channel: str, event_type: str, data: dict | None = None):
        """Publish event to Redis channel."""
        payload = {
            "type": event_type,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._redis.publish(channel, json.dumps(payload, ensure_ascii=False))
        logger.debug("event:%s on %s", event_type, channel)

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """Async generator that yields events from a Redis channel."""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON on channel %s", channel)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self):
        await self._redis.close()


# Global singleton
redis_event_bus = RedisEventBus()
