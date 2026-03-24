"""
Lightweight in-process event bus.
When scaling is needed, swap transport to Redis pub/sub — handlers stay the same.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger("shangtanai.events")

EventHandler = Callable[[Any], Coroutine]


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_type: str, handler: EventHandler):
        self._handlers[event_type].append(handler)

    async def emit(self, event_type: str, data: Any = None):
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return
        logger.info(f"event:{event_type}", extra={"handler_count": len(handlers)})
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")


# Global singleton
event_bus = EventBus()
