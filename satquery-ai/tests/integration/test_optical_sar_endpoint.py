"""Integration test for Optical + SAR multimodal analysis endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from tests.fixtures.synthetic_optical_sar import create_synthetic_optical_sar_pair

client = TestClient(app)


def test_optical_sar_endpoint(tmp_path: Path):
    # 1. Create synthetic Optical + SAR pair
    opt_p, sar_p = create_synthetic_optical_sar_pair(tmp_path, width=64, height=64)

    # 2. Ingest Optical
    with open(opt_p, "rb") as f:
        resp_opt = client.post(
            "/api/v1/images/inspect",
            files={"file": ("sentinel2_optical.tif", f, "image/tiff")},
        )
    assert resp_opt.status_code == 200
    opt_id = resp_opt.json()["id"]

    # 3. Ingest SAR
    with open(sar_p, "rb") as f:
        resp_sar = client.post(
            "/api/v1/images/inspect",
            files={"file": ("sentinel1_sar.tif", f, "image/tiff")},
        )
    assert resp_sar.status_code == 200
    sar_id = resp_sar.json()["id"]

    # 4. Run Optical + SAR Multimodal Analysis
    resp_fusion = client.post(
        "/api/v1/analysis/optical-sar",
        json={
            "optical_image_id": opt_id,
            "sar_image_id": sar_id,
        },
    )

    assert resp_fusion.status_code == 200
    data = resp_fusion.json()

    assert data["optical_image_id"] == opt_id
    assert data["sar_image_id"] == sar_id
    assert "corroboration_score" in data
    assert 0.0 <= data["corroboration_score"] <= 1.0
    assert "joint_claim" in data
    assert "optical_features" in data
    assert "sar_features" in data
    assert "evidence" in data
    assert data["evidence"]["id"].startswith("evi_")
    assert len(data["execution_steps"]) >= 3
