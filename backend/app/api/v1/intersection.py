from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.logging import log_operation
from app.models.requests import IntersectionRequest
from app.models.responses import IntersectionResponse
from app.services.overlay_service import intersect_features

router = APIRouter()


@router.post("/geometry/intersection", response_model=IntersectionResponse)
def intersection(req: IntersectionRequest, settings: Settings = Depends(get_settings)) -> IntersectionResponse:
    with log_operation("intersection", a_count=len(req.features_a), b_count=len(req.features_b)):
        results = intersect_features(
            req.features_a, req.features_b, req.min_area_m2, settings.default_min_intersection_area_m2
        )
    return IntersectionResponse(intersections=results)
