"""Benchmark execution API router."""

import asyncio

from fastapi import APIRouter, HTTPException

from ..models.schemas import BenchmarkRequest
from ..services.benchmark_runner import runner

router = APIRouter()


@router.post("/run")
async def run_benchmark(req: BenchmarkRequest):
    """Start a benchmark run. Returns job_id."""
    if req.framework not in ("sglang", "vllm", "ollama"):
        raise HTTPException(status_code=400, detail=f"Invalid framework: {req.framework}")

    job = runner.create_job(
        framework=req.framework,
        scenarios=req.scenarios,
        model=req.model,
        trials=req.trials,
    )
    # Fire and forget
    asyncio.create_task(runner.run_job(job))

    return {"job_id": job.job_id, "status": "running"}


@router.get("/status/{job_id}")
async def benchmark_status(job_id: str):
    """Get benchmark job status."""
    job = runner.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "framework": job.framework,
        "scenarios": job.scenarios,
        "model": job.model,
        "trials": job.trials,
        "log_lines": len(job.log_lines),
    }


@router.post("/cancel/{job_id}")
async def cancel_benchmark(job_id: str):
    """Cancel a running benchmark."""
    ok = await runner.cancel_job(job_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Job not running or not found")
    return {"job_id": job_id, "status": "cancelled"}
