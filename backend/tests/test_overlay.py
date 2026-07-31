"""Intersection and union — both net-new capabilities (no prior implementation existed on the frontend)."""
from app.services.overlay_service import intersect_features, union_features
from app.models.common import Feature


def _feat(fx: dict) -> Feature:
    return Feature(**fx)


def test_intersection_finds_real_overlap(overlapping_pair):
    result = intersect_features([_feat(overlapping_pair["a"])], [_feat(overlapping_pair["b"])],
                                 min_area_m2=None, default_min_area_m2=1.0)
    assert len(result) == 1
    assert result[0]["a_id"] == "ovl-a"
    assert result[0]["b_id"] == "ovl-b"
    assert result[0]["area_m2"] > 0


def test_intersection_excludes_shared_edge_only(adjacent_pair):
    result = intersect_features([_feat(adjacent_pair["a"])], [_feat(adjacent_pair["b"])],
                                 min_area_m2=None, default_min_area_m2=1.0)
    assert result == []  # sharing an edge is not an overlap


def test_intersection_min_area_filter(overlapping_pair):
    # Threshold above the real overlap area must exclude the result.
    result = intersect_features([_feat(overlapping_pair["a"])], [_feat(overlapping_pair["b"])],
                                 min_area_m2=10_000_000, default_min_area_m2=1.0)
    assert result == []


def test_union_area_less_than_sum_when_overlapping(overlapping_pair):
    from app.services.measure_service import compute_areas

    areas = compute_areas([_feat(overlapping_pair["a"]), _feat(overlapping_pair["b"])], crs="EPSG:4326")
    area_a, area_b = areas[0]["area_m2"], areas[1]["area_m2"]

    result = union_features([_feat(overlapping_pair["a"]), _feat(overlapping_pair["b"])])
    assert result["area_m2"] > max(area_a, area_b)          # bigger than either alone
    assert result["area_m2"] < area_a + area_b               # but less than the naive sum, because they overlap


def test_union_via_api(client, overlapping_pair):
    r = client.post("/v1/geometry/union", json={"features": [overlapping_pair["a"], overlapping_pair["b"]]})
    assert r.status_code == 200
    assert r.json()["area_m2"] > 0
