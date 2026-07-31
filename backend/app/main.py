"""
KEYMAP GIS Service — Phase 1.

Stateless FastAPI service exposing real Shapely/GeoPandas/GDAL/PROJ geometry
operations behind a versioned /v1/geometry/ API. No database, no
authentication (see SECURITY.md for what compensates for that this phase),
no features beyond the seven operations in the approved design document.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.errors import GeometryError
from app.core.logging import configure_logging, logger

settings = get_settings()
configure_logging()

app = FastAPI(
    title="KEYMAP GIS Service",
    version="0.1.0-phase1",
    description="Shapely/GeoPandas/GDAL/PROJ geometry operations for KEYMAP. Phase 1: no auth, no PostGIS.",
)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects oversized requests before they reach a handler. A bulk operation
    over thousands of plots is a multi-MB GeoJSON payload — this caps it so
    an oversized request fails fast and cleanly (413) rather than degrading
    the process. See ARCHITECTURE.md / SECURITY.md — this is a guardrail
    that stands in for real request-level controls until auth/rate-limiting
    exist in a later phase, not a substitute for them.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > settings.max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"error": {"code": "payload_too_large",
                                    "message": f"Request body exceeds {settings.max_body_bytes} bytes",
                                    "detail": {"content_length": int(content_length)}}},
            )
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)

# Never a wildcard — see SECURITY.md §CORS. With no authentication this
# phase, an open CORS policy plus an open API is the combination to avoid.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(GeometryError)
async def geometry_error_handler(request: Request, exc: GeometryError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "detail": exc.detail}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Geometry payload contents are intentionally not included here — see
    # core/logging.py and SECURITY.md §Logging.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred.", "detail": None}},
    )


app.include_router(v1_router)
