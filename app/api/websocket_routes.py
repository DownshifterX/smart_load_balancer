"""
app/api/websocket_routes.py
-----------------------------
WebSocket endpoint for real-time simulation updates.
Manages connected clients and broadcasts state every tick.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("WebSocket")

# Connected clients
connected_clients: set[WebSocket] = set()


async def broadcast(data: dict):
    """Broadcast state to all connected WebSocket clients."""
    if not connected_clients:
        return

    message = json.dumps(data)
    disconnected = set()

    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)

    # Clean up disconnected clients
    for client in disconnected:
        connected_clients.discard(client)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection handler."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total: {len(connected_clients)}")

    try:
        while True:
            # Listen for messages from client (for future bidirectional commands)
            data = await websocket.receive_text()
            # Could handle client commands here
            logger.debug(f"Received from client: {data}")
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total: {len(connected_clients)}")
    except Exception as e:
        connected_clients.discard(websocket)
        logger.error(f"WebSocket error: {e}")
