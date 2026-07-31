from fastapi import APIRouter

from app.api.v1 import area, buffer, distance, health, intersection, reproject, spatial_join, union

router = APIRouter(prefix="/v1")
router.include_router(health.router, tags=["health"])
router.include_router(buffer.router, tags=["geometry"])
router.include_router(spatial_join.router, tags=["geometry"])
router.include_router(intersection.router, tags=["geometry"])
router.include_router(union.router, tags=["geometry"])
router.include_router(area.router, tags=["geometry"])
router.include_router(distance.router, tags=["geometry"])
router.include_router(reproject.router, tags=["geometry"])
