import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket_manager import manager

logger = logging.getLogger("ws")
router = APIRouter()


@router.websocket("/ws/live")
async def live_feed(websocket: WebSocket):
    """
    Clients connect here and receive a JSON message for every new event as
    it happens: {"type": "event", "data": {...}}. The connection is
    receive-only from the client's point of view -- we still `receive_text`
    in a loop purely to detect disconnects promptly.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
