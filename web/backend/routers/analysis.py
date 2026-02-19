"""Analysis and hypothesis verification API router."""

from fastapi import APIRouter

from ..services.analysis_service import get_comparison_data, verify_hypotheses_structured
from ..services.result_loader import load_all_results

router = APIRouter()


@router.get("/hypotheses")
async def get_hypotheses():
    """Get H1-H5 hypothesis verification results as structured JSON."""
    data = load_all_results()
    return verify_hypotheses_structured(data)


@router.get("/report")
async def get_report():
    """Get comparison data for the frontend."""
    data = load_all_results()
    return get_comparison_data(data)
