"""Cross-cutting: the {"error": {code, message, detail}} shape and the guardrails from SECURITY.md."""
import app.main as main_module


def test_invalid_geometry_returns_standard_error_shape(client):
    r = client.post("/v1/geometry/area", json={
        "features": [{"id": "bad", "geometry": {"type": "Polygon", "coordinates": "not-coordinates"}}],
    })
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "invalid_geometry"
    assert body["error"]["detail"]["feature_id"] == "bad"


def test_empty_features_returns_400(client):
    r = client.post("/v1/geometry/area", json={"features": []})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "empty_input"


def test_body_size_limit_returns_413(client, monkeypatch):
    monkeypatch.setattr(main_module.settings, "max_body_bytes", 50)
    r = client.post("/v1/geometry/area", json={"features": [{"id": "x", "geometry": {"type": "Point", "coordinates": [0, 0]}}]})
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"


def test_cors_header_present_for_allowed_origin(client):
    r = client.get("/v1/health", headers={"Origin": "https://motaseemabdalla0-ux.github.io"})
    assert r.headers.get("access-control-allow-origin") == "https://motaseemabdalla0-ux.github.io"


def test_cors_rejects_unknown_origin(client):
    r = client.get("/v1/health", headers={"Origin": "https://evil.example.com"})
    # Starlette's CORSMiddleware simply omits the header for a disallowed
    # origin rather than erroring — a browser enforces the actual block.
    assert "access-control-allow-origin" not in r.headers
