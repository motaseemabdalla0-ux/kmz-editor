"""
Real geodesic-correct buffering, replacing the frontend's radial-vertex-offset
approximation (which self-intersects on concave polygons — see the Phase 0
report §2.3 and the architecture plan §3.2).

Approach: reproject to a metric CRS (auto-selected local UTM zone unless the
caller overrides it), run Shapely's real buffer with the requested cap/join
style, reproject the result back to the input CRS for output.
"""
from typing import List

from app.core.crs_utils import to_metric
from app.core.geometry_io import features_to_gdf, geometry_to_geojson
from app.models.common import Feature


def buffer_features(features: List[Feature], distance_m: float, cap_style: str, join_style: str, crs: str):
    gdf = features_to_gdf([f.model_dump() for f in features], crs=crs)
    metric_gdf, metric_crs = to_metric(gdf)

    buffered = metric_gdf.geometry.buffer(distance_m, cap_style=cap_style, join_style=join_style)
    areas_m2 = buffered.area

    result_gdf = metric_gdf.set_geometry(buffered).to_crs(crs)

    return [
        {
            "id": row_id,
            "geometry": geometry_to_geojson(geom),
            "area_m2": round(float(area), 3),
        }
        for row_id, geom, area in zip(gdf["id"], result_gdf.geometry, areas_m2)
    ]
