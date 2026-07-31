from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import UnionRequest
from app.models.responses import UnionResponse
from app.services.overlay_service import union_features

router = APIRouter()


@router.post("/geometry/union", response_model=UnionResponse)
def union(req: UnionRequest) -> UnionResponse:
    with log_operation("union", feature_count=len(req.features)):
        result = union_features(req.features)
    return UnionResponse(**result)
