"""Integration tests for STAC search and Analysis Replay endpoints."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_stac_search_endpoint():
    resp = client.post(
        "/api/v1/stac/search",
        json={
            "bbox": [78.40, 17.30, 78.55, 17.45],
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "collection": "sentinel-2-l2a",
            "max_cloud_cover": 25.0,
            "limit": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "items" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "id" in item
    assert "cloud_cover" in item
    assert "ranking_score" in item
    assert "assets" in item


def test_models_manifest_endpoint():
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "manifest" in data
    assert "hardware" in data
    if data["manifest"]:
        assert "host_hardware" in data["manifest"]
        assert "models" in data["manifest"]


def test_analysis_replay_endpoint():
    resp = client.post("/api/v1/analysis/latest/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("REPRODUCED", "DIFFERENT")
    assert "checks" in data
    assert data["checks"]["inputs"] == "PASSED"
    assert data["checks"]["models"] == "PASSED"
    assert data["checks"]["parameters"] == "PASSED"
