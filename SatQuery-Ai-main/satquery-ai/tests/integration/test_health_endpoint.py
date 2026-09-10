"""Integration tests for health endpoints."""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "satquery-api"


def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "satquery-api"
    assert data["version"] == "0.1.0"
    assert "hardware" in data
