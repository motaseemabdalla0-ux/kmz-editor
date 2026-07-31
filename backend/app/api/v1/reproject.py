from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import ReprojectRequest
from app.models.responses import ReprojectResponse
from app.services.crs_service import reproject_features

router = APIRouter()


@router.post("/geometry/reproject", response_model=ReprojectResponse)
def reproject(req: ReprojectRequest) -> ReprojectResponse:
    with log_operation("reproject", feature_count=len(req.features)):
        features = reproject_features(req.features, req.source_crs, req.target_crs)
    return ReprojectResponse(features=features, target_crs=req.target_crs)
