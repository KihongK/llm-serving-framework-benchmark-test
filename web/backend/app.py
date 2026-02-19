"""FastAPI application — CORS, static files, lifespan."""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on sys.path so bench.* imports work
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from .routers import analysis, benchmark, results, server
from .services.benchmark_runner import runner
from .services.server_manager import server_manager
from .ws import benchmark_ws, monitor_ws, server_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    await server_manager.detect_external_servers()
    yield
    await runner.cancel_all()
    await server_manager.stop_server(force=True)


app = FastAPI(
    title="LLM Benchmark Web GUI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routers
app.include_router(results.router, prefix="/api/v1/results", tags=["results"])
app.include_router(server.router, prefix="/api/v1/server", tags=["server"])
app.include_router(benchmark.router, prefix="/api/v1/benchmark", tags=["benchmark"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

# WebSocket endpoints
app.include_router(benchmark_ws.router, tags=["ws"])
app.include_router(monitor_ws.router, tags=["ws"])
app.include_router(server_ws.router, tags=["ws"])

# Serve frontend build (production)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(frontend_dist):
    from fastapi.responses import FileResponse

    # Serve static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA index.html for all non-API routes."""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
