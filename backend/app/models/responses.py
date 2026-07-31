from typing import List, Optional

from pydantic import BaseModel

from app.models.common import GeoJSONGeometry, WGS84


class BufferResult(BaseModel):
    id: str
    geometry: GeoJSONGeometry
    area_m2: float


class BufferResponse(BaseModel):
    results: List[BufferResult]
    crs: str = WGS84


class JoinMatch(BaseModel):
    target_id: str
    source_id: str
    value: object


class SpatialJoinResponse(BaseModel):
    matches: List[JoinMatch]
    matched_count: int
    target_count: int
    unmatched_target_ids: List[str]


class IntersectionResult(BaseModel):
    a_id: str
    b_id: str
    geometry: GeoJSONGeometry
    area_m2: float


class IntersectionResponse(BaseModel):
    intersections: List[IntersectionResult]


class UnionResponse(BaseModel):
    geometry: GeoJSONGeometry
    area_m2: float


class AreaResult(BaseModel):
    id: str
    area_m2: float
    area_ha: float


class AreaResponse(BaseModel):
    results: List[AreaResult]


class DistanceResponse(BaseModel):
    distance_m: float


class ReprojectResponse(BaseModel):
    features: List[dict]
    target_crs: str
