"""
Real polygon overlay — intersection and union. Neither had a correct
implementation on the frontend before this backend existed: overlap
"detection" was a centroid-containment heuristic, and union did not exist
at all (net-new capability, per the API design doc §3.5).
"""
from typing import List, Optional

import geopandas as gpd

from app.core.crs_utils import to_metric
from app.core.geometry_io import features_to_gdf, geometry_to_geojson
from app.models.common import Feature


def intersect_features(features_a: List[Feature], features_b: List[Feature], min_area_m2: Optional[float],
                        default_min_area_m2: float):
    threshold = min_area_m2 if min_area_m2 is not None else default_min_area_m2

    gdf_a = features_to_gdf([f.model_dump() for f in features_a]).rename(columns={"id": "a_id"})[["a_id", "geometry"]]
    gdf_b = features_to_gdf([f.model_dump() for f in features_b]).rename(columns={"id": "b_id"})[["b_id", "geometry"]]

    # Overlay in a shared metric CRS so the min_area_m2 filter and the
    # returned area are both real square metres, not degree^2 nonsense.
    combined = gpd.GeoDataFrame(
        {"id": list(gdf_a["a_id"]) + list(gdf_b["b_id"])},
        geometry=list(gdf_a.geometry) + list(gdf_b.geometry),
        crs=gdf_a.crs,
    )
    _, metric_crs = to_metric(combined)
    gdf_a_m = gdf_a.to_crs(metric_crs)
    gdf_b_m = gdf_b.to_crs(metric_crs)

    overlay = gpd.overlay(gdf_a_m, gdf_b_m, how="intersection", keep_geom_type=True)
    if overlay.empty:
        return []

    overlay["area_m2"] = overlay.geometry.area
    overlay = overlay[overlay["area_m2"] >= threshold]
    overlay_wgs84 = overlay.to_crs(gdf_a.crs)

    return [
        {
            "a_id": row["a_id"],
            "b_id": row["b_id"],
            "geometry": geometry_to_geojson(geom),
            "area_m2": round(float(area), 3),
        }
        for (_, row), geom, area in zip(overlay.iterrows(), overlay_wgs84.geometry, overlay["area_m2"])
    ]


def union_features(features: List[Feature]):
    gdf = features_to_gdf([f.model_dump() for f in features])
    metric_gdf, _ = to_metric(gdf)

    unified_metric = metric_gdf.geometry.union_all()
    area_m2 = unified_metric.area

    unified_wgs84 = gpd.GeoSeries([unified_metric], crs=metric_gdf.crs).to_crs(gdf.crs).iloc[0]

    return {"geometry": geometry_to_geojson(unified_wgs84), "area_m2": round(float(area_m2), 3)}
