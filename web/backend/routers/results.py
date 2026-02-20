"""Results API router."""

from fastapi import APIRouter, HTTPException

from ..services.result_loader import (
    clear_all_results,
    clear_framework_results,
    list_result_files,
    load_all_results,
    load_framework_results,
)

router = APIRouter()


@router.get("/")
async def get_result_files():
    """List result files per framework."""
    return list_result_files()


@router.get("/all")
async def get_all_results():
    """Load all results."""
    return load_all_results()


@router.delete("/all")
async def delete_all_results():
    """Delete all results for all frameworks."""
    deleted = clear_all_results()
    return {"deleted": deleted}


@router.delete("/{framework}")
async def delete_framework_results(framework: str):
    """Delete results for a specific framework."""
    count = clear_framework_results(framework)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"No results for {framework}")
    return {"framework": framework, "deleted_files": count}


@router.get("/{framework}")
async def get_framework_results(framework: str):
    """Load results for a specific framework."""
    data = load_framework_results(framework)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No results for {framework}")
    return data
