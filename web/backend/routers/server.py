"""Server health, GPU monitoring, and server lifecycle API router."""

from fastapi import APIRouter, HTTPException

from ..config import FRAMEWORKS
from ..models.schemas import ServerStartRequest, ServerStopRequest
from ..services.server_monitor import check_all_health, get_gpu_stats
from ..services.server_manager import server_manager

router = APIRouter()


@router.get("/health")
async def server_health():
    """Check health of all 3 framework servers."""
    return await check_all_health()


@router.get("/gpu")
async def gpu_status():
    """Get current GPU stats."""
    return get_gpu_stats()


@router.get("/managed")
async def managed_server_status():
    """Get the status of the currently managed server."""
    return server_manager.get_status()


@router.post("/start")
async def start_server(req: ServerStartRequest):
    """Start a framework server."""
    if req.framework not in FRAMEWORKS:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {req.framework}")
    try:
        await server_manager.start_server(req.framework, req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return server_manager.get_status()


@router.post("/stop")
async def stop_server(req: ServerStopRequest | None = None):
    """Stop the currently running server."""
    force = req.force if req else False
    try:
        await server_manager.stop_server(force=force)
    except RuntimeError as e:
        if "BENCHMARK_RUNNING" in str(e):
            raise HTTPException(
                status_code=409,
                detail="벤치마크가 실행 중입니다. 먼저 벤치마크를 취소하세요.",
            )
        raise HTTPException(status_code=500, detail=str(e))
    return server_manager.get_status()
