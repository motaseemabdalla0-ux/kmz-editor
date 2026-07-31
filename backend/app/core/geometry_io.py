"""
The GeoJSON <-> Shapely/GeoPandas conversion boundary. This is the module the
architecture plan flagged as the real integration risk (§7 of the design
doc): Shapely itself is trustworthy, but the glue code around it — id
preservation across a batch, malformed-input handling — is exactly the kind
of thing that needs its own tests, not just trust in the underlying library.
"""
from typing import Any, Dict, List, Optional

import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.geometry.base import BaseGeometry

from app.core.errors import invalid_geometry, empty_input

WGS84 = "EPSG:4326"


def parse_geometry(raw: Dict[str, Any], feature_id: Optional[str] = None) -> BaseGeometry:
    """A single raw GeoJSON geometry dict -> a validated Shapely geometry."""
    if not isinstance(raw, dict) or "type" not in raw:
        raise invalid_geometry("not a GeoJSON geometry object", feature_id)
    try:
        geom = shape(raw)
    except Exception as exc:  # shapely raises a variety of exception types here
        raise invalid_geometry(str(exc), feature_id) from exc
    if geom.is_empty:
        raise invalid_geometry("geometry is empty", feature_id)
    if not geom.is_valid:
        # Attempt the standard zero-width-buffer repair before giving up —
        # this fixes the common self-touching-ring case from hand-digitized
        # KML exports without silently accepting genuinely broken input.
        repaired = geom.buffer(0)
        if repaired.is_valid and not repaired.is_empty:
            geom = repaired
        else:
            raise invalid_geometry("geometry is topologically invalid and could not be auto-repaired", feature_id)
    return geom


def geometry_to_geojson(geom: BaseGeometry) -> Dict[str, Any]:
    return mapping(geom)


def features_to_gdf(features: List[Dict[str, Any]], crs: str = WGS84) -> gpd.GeoDataFrame:
    """
    [{id, geometry, properties?}, ...] -> a GeoDataFrame with an explicit
    `id` column (kept as plain data, never as the pandas index) so a
    filter/dissolve/join operation can't silently lose or reorder it.
    """
    if not features:
        raise empty_input("features")
    ids, geoms, props = [], [], []
    for f in features:
        fid = f.get("id")
        ids.append(fid)
        geoms.append(parse_geometry(f.get("geometry"), fid))
        props.append(f.get("properties") or {})
    gdf = gpd.GeoDataFrame({"id": ids, **_transpose_props(props)}, geometry=geoms, crs=crs)
    return gdf


def _transpose_props(props: List[Dict[str, Any]]) -> Dict[str, list]:
    """Turn a list of per-feature property dicts into GeoDataFrame columns."""
    keys = set()
    for p in props:
        keys.update(p.keys())
    return {k: [p.get(k) for p in props] for k in keys}


def gdf_to_features(gdf: gpd.GeoDataFrame, extra_cols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    out = []
    for _, row in gdf.iterrows():
        item = {"id": row["id"], "geometry": geometry_to_geojson(row.geometry)}
        for col in extra_cols or []:
            if col in row:
                item[col] = row[col]
        out.append(item)
    return out
