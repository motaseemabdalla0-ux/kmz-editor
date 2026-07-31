from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import SpatialJoinRequest
from app.models.responses import SpatialJoinResponse
from app.services.join_service import spatial_join

router = APIRouter()


@router.post("/geometry/spatial-join", response_model=SpatialJoinResponse)
def join(req: SpatialJoinRequest) -> SpatialJoinResponse:
    with log_operation("spatial_join", source_count=len(req.source_features), target_count=len(req.target_features)):
        result = spatial_join(req.source_features, req.target_features, req.field, req.predicate)
    return SpatialJoinResponse(**result)
