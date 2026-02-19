"""GPU monitoring WebSocket — 2-second interval polling."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.server_monitor import get_gpu_stats

router = APIRouter()


@router.websocket("/ws/gpu")
async def gpu_monitor_stream(websocket: WebSocket):
    """Stream GPU stats every 2 seconds."""
    await websocket.accept()
    try:
        while True:
            stats = get_gpu_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
