"""Integration test for Bi-Temporal Change Detection endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from tests.fixtures.synthetic_bitemporal import create_synthetic_bitemporal_pair

client = TestClient(app)


def test_bitemporal_change_endpoint(tmp_path: Path):
    # 1. Generate synthetic before/after GeoTIFF pair
    before_p, after_p = create_synthetic_bitemporal_pair(tmp_path, width=64, height=64, change_box_size=16)

    # 2. Ingest Before image
    with open(before_p, "rb") as f:
        resp_b = client.post(
            "/api/v1/images/inspect",
            files={"file": ("before.tif", f, "image/tiff")},
        )
    assert resp_b.status_code == 200
    img_before_id = resp_b.json()["id"]

    # 3. Ingest After image
    with open(after_p, "rb") as f:
        resp_a = client.post(
            "/api/v1/images/inspect",
            files={"file": ("after.tif", f, "image/tiff")},
        )
    assert resp_a.status_code == 200
    img_after_id = resp_a.json()["id"]

    # 4. Run Change Analysis
    change_resp = client.post(
        "/api/v1/analysis/change",
        json={
            "image_before_id": img_before_id,
            "image_after_id": img_after_id,
            "threshold": 0.5,
        },
    )

    assert change_resp.status_code == 200
    data = change_resp.json()

    assert data["image_before_id"] == img_before_id
    assert data["image_after_id"] == img_after_id
    assert "change_percent" in data
    assert "total_area_m2" in data
    assert "regions_geojson" in data
    assert "mask_preview_url" in data
    assert "evidence" in data
    assert data["evidence"]["id"].startswith("evi_")
    assert len(data["execution_steps"]) >= 4

    # 5. Fetch change mask overlay
    mask_resp = client.get(data["mask_preview_url"])
    assert mask_resp.status_code == 200
    assert mask_resp.headers["content-type"] == "image/png"
