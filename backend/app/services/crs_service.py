"""
CRS transformation — built ahead of its UI trigger (see the API design doc
§3.8): no KEYMAP import path produces non-WGS84 data yet (KML is always
WGS84), but Shapefile import in a later phase commonly will be, and this
endpoint is what makes that a frontend-only addition when it lands.
"""
from typing import List

from pyproj.exceptions import CRSError

from app.core.crs_utils import validate_crs
from app.core.errors import unknown_crs
from app.core.geometry_io import features_to_gdf, gdf_to_features
from app.models.common import Feature


def _validate_or_raise(crs: str) -> None:
    try:
        validate_crs(crs)
    except CRSError as exc:
        raise unknown_crs(crs) from exc


def reproject_features(features: List[Feature], source_crs: str, target_crs: str):
    _validate_or_raise(source_crs)
    _validate_or_raise(target_crs)
    gdf = features_to_gdf([f.model_dump() for f in features], crs=source_crs)
    reprojected = gdf.to_crs(target_crs)
    return gdf_to_features(reprojected)
