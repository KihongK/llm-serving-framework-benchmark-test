"""Benchmark log streaming WebSocket."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.benchmark_runner import runner

router = APIRouter()


@router.websocket("/ws/benchmark/{job_id}")
async def benchmark_log_stream(websocket: WebSocket, job_id: str):
    """Stream benchmark logs in real-time."""
    await websocket.accept()

    q = runner.subscribe(job_id)
    if q is None:
        await websocket.send_json({"type": "error", "data": "Job not found"})
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
