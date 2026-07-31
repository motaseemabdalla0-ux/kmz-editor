"""
The defect this fixes: the frontend tested "is the TARGET's centroid inside
the SOURCE polygon" — which misses a target that genuinely overlaps a
source at one corner while its own centroid sits far outside it. This test
constructs exactly that case.
"""
from app.services.join_service import spatial_join
from app.models.common import Feature


def test_join_catches_overlap_missed_by_centroid_test():
    # Small source polygon with the field we're copying.
    source = Feature(
        id="S1",
        geometry={"type": "Polygon", "coordinates": [[
            [37.9000, 26.6000], [37.9010, 26.6000], [37.9010, 26.6010], [37.9000, 26.6010], [37.9000, 26.6000]
        ]]},
        properties={"District": "Zone1"},
    )
    # Large target rectangle: overlaps the source only in its bottom-left
    # corner, but its centroid (~37.925, ~26.625) is nowhere near the
    # source. A centroid-in-polygon test would find no match; a real
    # intersects() test must.
    target = Feature(
        id="T1",
        geometry={"type": "Polygon", "coordinates": [[
            [37.9005, 26.6005], [37.9500, 26.6005], [37.9500, 26.6500], [37.9005, 26.6500], [37.9005, 26.6005]
        ]]},
    )
    result = spatial_join([source], [target], field="District", predicate="intersects")
    assert result["matched_count"] == 1
    assert result["matches"][0] == {"target_id": "T1", "source_id": "S1", "value": "Zone1"}
    assert result["unmatched_target_ids"] == []


def test_join_no_overlap_is_unmatched(adjacent_pair):
    source = Feature(id=adjacent_pair["a"]["id"], geometry=adjacent_pair["a"]["geometry"], properties={"District": "A"})
    target = Feature(
        id="far-away",
        geometry={"type": "Polygon", "coordinates": [[
            [38.5, 27.5], [38.51, 27.5], [38.51, 27.51], [38.5, 27.51], [38.5, 27.5]
        ]]},
    )
    result = spatial_join([source], [target], field="District", predicate="intersects")
    assert result["matched_count"] == 0
    assert result["unmatched_target_ids"] == ["far-away"]


def test_join_via_api(client):
    source = {
        "id": "S1",
        "geometry": {"type": "Polygon", "coordinates": [[
            [37.9, 26.6], [37.91, 26.6], [37.91, 26.61], [37.9, 26.61], [37.9, 26.6]
        ]]},
        "properties": {"District": "North"},
    }
    target = {
        "id": "T1",
        "geometry": {"type": "Polygon", "coordinates": [[
            [37.905, 26.605], [37.915, 26.605], [37.915, 26.615], [37.905, 26.615], [37.905, 26.605]
        ]]},
    }
    r = client.post("/v1/geometry/spatial-join", json={
        "source_features": [source], "target_features": [target], "field": "District",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["matched_count"] == 1
    assert body["matches"][0]["value"] == "North"
