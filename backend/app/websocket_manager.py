import asyncio
import json
import logging

from fastapi import WebSocket

from app.config import settings

logger = logging.getLogger("websocket_manager")

REDIS_CHANNEL = "analytics:live_events"


class ConnectionManager:
    """
    Tracks connected WebSocket clients for this process and broadcasts
    messages to all of them.

    Two modes:
      - No Redis configured: fake_data.generator() calls broadcast()
        directly. Works great for a single backend instance (the common
        local-dev / demo case).
      - Redis configured: broadcast() PUBLISHes to a Redis channel instead
        of pushing to sockets directly, and a background subscriber task
        (started in main.py) forwards every message it receives to the
        local connections. This is what lets you run several backend
        replicas behind a load balancer and still have every client see
        every event, which is the whole reason Redis pub/sub shows up in
        real-time dashboard architectures.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._redis = None

    async def startup(self) -> None:
        if settings.redis_url:
            import redis.asyncio as redis

            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            asyncio.create_task(self._redis_listener())
            logger.info("WebSocket manager using Redis pub/sub at %s", settings.redis_url)
        else:
            logger.info("WebSocket manager using in-memory broadcast (no REDIS_URL set)")

    async def shutdown(self) -> None:
        if self._redis:
            await self._redis.close()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload, default=str)
        if self._redis:
            await self._redis.publish(REDIS_CHANNEL, message)
        else:
            await self._send_to_local_clients(message)

    async def _send_to_local_clients(self, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def _redis_listener(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            await self._send_to_local_clients(message["data"])


manager = ConnectionManager()
