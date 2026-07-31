"""
CRS transformation — built ahead of its UI trigger. The meaningful
correctness test is a round trip: reproject to a projected CRS and back,
coordinates should return to (very nearly) where they started.
"""
import pytest

from app.core.crs_utils import utm_epsg_for_lonlat
from app.core.errors import GeometryError
from app.services.crs_service import reproject_features
from app.models.common import Feature


def test_utm_zone_for_alula():
    # AlUla is ~37.9E, 26.6N -> UTM zone 37N.
    assert utm_epsg_for_lonlat(37.9, 26.6) == "EPSG:32637"


def test_reproject_round_trip(known_area_square):
    original = Feature(**known_area_square)
    to_utm = reproject_features([original], source_crs="EPSG:4326", target_crs="EPSG:32637")
    back_to_wgs84 = reproject_features(
        [Feature(id=to_utm[0]["id"], geometry=to_utm[0]["geometry"])],
        source_crs="EPSG:32637", target_crs="EPSG:4326",
    )
    orig_coords = original.geometry["coordinates"][0][0]
    round_tripped_coords = back_to_wgs84[0]["geometry"]["coordinates"][0][0]
    assert orig_coords[0] == pytest.approx(round_tripped_coords[0], abs=1e-6)
    assert orig_coords[1] == pytest.approx(round_tripped_coords[1], abs=1e-6)


def test_unknown_crs_rejected(known_area_square):
    with pytest.raises(GeometryError) as exc_info:
        reproject_features([Feature(**known_area_square)], source_crs="EPSG:4326", target_crs="NOT-A-CRS")
    assert exc_info.value.code == "unknown_crs"


def test_reproject_via_api(client, known_area_square):
    r = client.post("/v1/geometry/reproject", json={
        "features": [known_area_square], "source_crs": "EPSG:4326", "target_crs": "EPSG:32637",
    })
    assert r.status_code == 200
    assert r.json()["target_crs"] == "EPSG:32637"


def test_reproject_bad_crs_via_api_returns_400(client, known_area_square):
    r = client.post("/v1/geometry/reproject", json={
        "features": [known_area_square], "source_crs": "EPSG:4326", "target_crs": "NOT-A-CRS",
    })
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "unknown_crs"
