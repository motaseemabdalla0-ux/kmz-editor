"""
Real projected-CRS area and distance, replacing the frontend's
spherical-excess area approximation used for the KPI strip / stats panel.

Note on scope (see the API design doc §3.7): this backend's /distance
endpoint serves bulk/programmatic use, not the live drag-to-measure map HUD
— that interaction stays client-side on haversine math, since a per-mouse-
move HTTP round trip would make that tool feel broken. This is the same
design decision restated where it's implemented, not just where it was
proposed.
"""
from typing import List

import geopandas as gpd

from app.core.crs_utils import to_metric
from app.core.geometry_io import features_to_gdf, parse_geometry
from app.models.common import Feature, GeoJSONGeometry


def compute_areas(features: List[Feature], crs: str):
    gdf = features_to_gdf([f.model_dump() for f in features], crs=crs)
    metric_gdf, _ = to_metric(gdf)
    areas_m2 = metric_gdf.geometry.area
    return [
        {"id": row_id, "area_m2": round(float(a), 3), "area_ha": round(float(a) / 10000.0, 5)}
        for row_id, a in zip(gdf["id"], areas_m2)
    ]


def compute_distance(geometry_a: GeoJSONGeometry, geometry_b: GeoJSONGeometry, crs: str) -> float:
    geom_a = parse_geometry(geometry_a, "geometry_a")
    geom_b = parse_geometry(geometry_b, "geometry_b")
    pair = gpd.GeoDataFrame({"id": ["a", "b"]}, geometry=[geom_a, geom_b], crs=crs)
    metric_pair, _ = to_metric(pair)
    return round(float(metric_pair.geometry.iloc[0].distance(metric_pair.geometry.iloc[1])), 3)
