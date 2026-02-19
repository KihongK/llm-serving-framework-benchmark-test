"""Results API router."""

from fastapi import APIRouter, HTTPException

from ..services.result_loader import list_result_files, load_all_results, load_framework_results

router = APIRouter()


@router.get("/")
async def get_result_files():
    """List result files per framework."""
    return list_result_files()


@router.get("/all")
async def get_all_results():
    """Load all results."""
    return load_all_results()


@router.get("/{framework}")
async def get_framework_results(framework: str):
    """Load results for a specific framework."""
    data = load_framework_results(framework)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No results for {framework}")
    return data
