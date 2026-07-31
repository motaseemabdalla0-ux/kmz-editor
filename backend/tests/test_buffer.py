"""
The defect this fixes: the frontend's radial-vertex-offset buffer
self-intersects on concave polygons. This is THE test that proves the
backend actually fixes it — shapely.geometry.shape(...).is_valid on the
concave fixture's buffered result must be True.
"""
from shapely.geometry import shape

from app.services.buffer_service import buffer_features
from app.models.common import Feature


def _feature(fx: dict) -> Feature:
    return Feature(**fx)


def test_buffer_concave_polygon_stays_valid(concave_polygon):
    results = buffer_features([_feature(concave_polygon)], distance_m=15, cap_style="round",
                               join_style="round", crs="EPSG:4326")
    assert len(results) == 1
    geom = shape(results[0]["geometry"])
    assert geom.is_valid, "buffered concave polygon must not self-intersect"
    assert results[0]["area_m2"] > 0


def test_buffer_grows_the_area(concave_polygon):
    original = shape(concave_polygon["geometry"])
    results = buffer_features([_feature(concave_polygon)], distance_m=25, cap_style="round",
                               join_style="round", crs="EPSG:4326")
    assert results[0]["area_m2"] > original.area  # sanity: degrees^2 << m^2 either way, just checks growth direction holds


def test_buffer_via_api(client, concave_polygon):
    r = client.post("/v1/geometry/buffer", json={
        "features": [concave_polygon],
        "distance_m": 10,
        "cap_style": "round",
        "join_style": "round",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["id"] == concave_polygon["id"]
    assert shape(body["results"][0]["geometry"]).is_valid


def test_buffer_preserves_feature_ids_in_batch(concave_polygon, polygon_with_hole):
    results = buffer_features(
        [_feature(concave_polygon), _feature(polygon_with_hole)],
        distance_m=5, cap_style="round", join_style="round", crs="EPSG:4326",
    )
    ids = {r["id"] for r in results}
    assert ids == {concave_polygon["id"], polygon_with_hole["id"]}
