"""
Real projected-CRS area/distance, replacing the frontend's spherical-excess
approximation. The known-area fixture's expected value is a tolerance band,
not an exact number — see fixtures/known_area_square.json's _note for why.
"""
from app.services.measure_service import compute_areas, compute_distance
from app.models.common import Feature


def test_known_area_square_within_tolerance(known_area_square):
    result = compute_areas([Feature(id=known_area_square["id"], geometry=known_area_square["geometry"])],
                            crs="EPSG:4326")
    area = result[0]["area_m2"]
    assert 9900 <= area <= 10100, f"expected ~10,000 m2, got {area}"


def test_concave_polygon_area_is_positive_and_bounded(concave_polygon):
    result = compute_areas([Feature(**concave_polygon)], crs="EPSG:4326")
    area = result[0]["area_m2"]
    assert area > 0
    # The L-shape's bounding box is 0.003 x 0.003 degrees ~= 333m x 300m at
    # this latitude; the true area must be smaller than that box.
    assert area < 333 * 300


def test_distance_between_known_points():
    # Same ~100m offset used to build the known-area-square fixture.
    a = {"type": "Point", "coordinates": [37.9000000, 26.6000000]}
    b = {"type": "Point", "coordinates": [37.9010048, 26.6000000]}
    d = compute_distance(a, b, crs="EPSG:4326")
    assert 95 <= d <= 105, f"expected ~100m, got {d}"


def test_area_via_api(client, known_area_square):
    r = client.post("/v1/geometry/area", json={"features": [known_area_square]})
    assert r.status_code == 200
    assert 9900 <= r.json()["results"][0]["area_m2"] <= 10100
