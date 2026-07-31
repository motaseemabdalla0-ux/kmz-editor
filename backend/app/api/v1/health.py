from fastapi import APIRouter

from app.models.common import HealthResponse

router = APIRouter()

SERVICE_VERSION = "0.1.0-phase1"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=SERVICE_VERSION)
