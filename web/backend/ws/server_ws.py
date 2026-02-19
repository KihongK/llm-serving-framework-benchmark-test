"""Server log streaming WebSocket."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.server_manager import server_manager

router = APIRouter()


@router.websocket("/ws/server/logs")
async def server_log_stream(websocket: WebSocket):
    """Stream server startup and runtime logs in real-time."""
    await websocket.accept()

    q = server_manager.subscribe()
    if q is None:
        await websocket.send_json({"type": "error", "data": "No server running"})
        await websocket.close()
        return

    try:
        while True:
            line = await q.get()
            if line is None:
                await websocket.send_json({"type": "done", "data": ""})
                break
            await websocket.send_json({"type": "log", "data": line})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
