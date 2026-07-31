from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import DistanceRequest
from app.models.responses import DistanceResponse
from app.services.measure_service import compute_distance

router = APIRouter()


@router.post("/geometry/distance", response_model=DistanceResponse)
def distance(req: DistanceRequest) -> DistanceResponse:
    with log_operation("distance"):
        d = compute_distance(req.geometry_a, req.geometry_b, req.crs)
    return DistanceResponse(distance_m=d)
