from fastapi import APIRouter

from app.core.logging import log_operation
from app.models.requests import BufferRequest
from app.models.responses import BufferResponse
from app.services.buffer_service import buffer_features

router = APIRouter()


@router.post("/geometry/buffer", response_model=BufferResponse)
def buffer(req: BufferRequest) -> BufferResponse:
    with log_operation("buffer", feature_count=len(req.features)):
        results = buffer_features(req.features, req.distance_m, req.cap_style, req.join_style, req.crs)
    return BufferResponse(results=results, crs=req.crs)
