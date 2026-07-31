from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.common import Feature, GeoJSONGeometry, WGS84


class BufferRequest(BaseModel):
    features: List[Feature]
    distance_m: float
    cap_style: str = Field(default="round", pattern="^(round|flat|square)$")
    join_style: str = Field(default="round", pattern="^(round|mitre|bevel)$")
    crs: str = WGS84


class SpatialJoinRequest(BaseModel):
    source_features: List[Feature]
    target_features: List[Feature]
    field: str
    predicate: str = Field(default="intersects", pattern="^(intersects|within|contains)$")


class IntersectionRequest(BaseModel):
    features_a: List[Feature]
    features_b: List[Feature]
    min_area_m2: Optional[float] = None  # falls back to settings.default_min_intersection_area_m2


class UnionRequest(BaseModel):
    features: List[Feature]


class AreaRequest(BaseModel):
    features: List[Feature]
    crs: str = WGS84


class DistanceRequest(BaseModel):
    geometry_a: GeoJSONGeometry
    geometry_b: GeoJSONGeometry
    crs: str = WGS84


class ReprojectRequest(BaseModel):
    features: List[Feature]
    source_crs: str
    target_crs: str = WGS84
