from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import AreaRequest
from app.models.responses import AreaResponse
from app.services.measure_service import compute_areas

router = APIRouter()


@router.post("/geometry/area", response_model=AreaResponse)
def area(req: AreaRequest) -> AreaResponse:
    with log_operation("area", feature_count=len(req.features)):
        results = compute_areas(req.features, req.crs)
    return AreaResponse(results=results)
