"""
CRS handling. Two distinct jobs, per the design doc:

1. Auto-select a metric (projected) CRS for operations that need real
   meters — buffer distance, area, distance — replacing the spherical-excess
   *approximation* the frontend used before this backend existed. WGS84
   (EPSG:4326) is an angular CRS; you cannot correctly buffer or measure area
   in it directly, which was the root cause of the accuracy defects this
   phase exists to fix.
2. Reproject on request for /geometry/reproject (source SHP/DXF data is
   commonly delivered in a local UTM zone, not WGS84 — this is the CRS
   transformation contract from the API design doc, ahead of its UI trigger).
"""
import geopandas as gpd
from pyproj import CRS

WGS84 = "EPSG:4326"


def utm_epsg_for_lonlat(lon: float, lat: float) -> str:
    """
    Standard UTM zone formula. Saudi Arabia (and therefore AlUla) spans UTM
    zones 36N-39N; this is general-purpose, not hardcoded to that range, so
    the same service works correctly if KEYMAP is ever pointed at data
    elsewhere.
    """
    zone = int((lon + 180) / 6) + 1
    zone = max(1, min(60, zone))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return f"EPSG:{epsg}"


def auto_metric_crs(gdf: gpd.GeoDataFrame) -> str:
    """Pick a UTM zone from the centroid of the union of all geometries."""
    src = gdf if gdf.crs else gdf.set_crs(WGS84)
    wgs84 = src.to_crs(WGS84) if src.crs.to_string() != WGS84 else src
    centroid = wgs84.union_all().centroid
    return utm_epsg_for_lonlat(centroid.x, centroid.y)


def to_metric(gdf: gpd.GeoDataFrame, target_crs: str | None = None) -> tuple[gpd.GeoDataFrame, str]:
    """Reproject to a metric CRS — the caller's explicit choice if given,
    otherwise an auto-selected local UTM zone. Returns (projected_gdf, crs_used)."""
    crs_used = target_crs or auto_metric_crs(gdf)
    return gdf.to_crs(crs_used), crs_used


def validate_crs(crs: str) -> str:
    """Raises pyproj.exceptions.CRSError (caught by the router) if unrecognized."""
    CRS.from_user_input(crs)
    return crs
