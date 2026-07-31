"""Shared shapes used across more than one endpoint's request/response models."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

WGS84 = "EPSG:4326"

# Kept loose (Dict[str, Any]) rather than depending on a full GeoJSON pydantic
# library — Phase 1 scope is the seven geometry operations, not a general
# GeoJSON validation layer. app/core/geometry_io.py is what actually
# validates convertibility to a real geometry, and raises a clean 400 on
# anything this permissive typing lets through but Shapely rejects.
GeoJSONGeometry = Dict[str, Any]


class Feature(BaseModel):
    id: str
    geometry: GeoJSONGeometry
    properties: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


CapStyle = Field(default="round", pattern="^(round|flat|square)$")
JoinStyle = Field(default="round", pattern="^(round|mitre|bevel)$")
Predicate = Field(default="intersects", pattern="^(intersects|within|contains)$")
