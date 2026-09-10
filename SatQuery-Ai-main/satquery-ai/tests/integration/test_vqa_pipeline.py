"""Integration test for Single-Image VQA endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_vqa_pipeline_endpoint(tmp_path: Path):
    # 1. Ingest image
    tif_file = tmp_path / "scene_vqa.tif"
    create_synthetic_multiband_geotiff(tif_file, width=64, height=64, bands=4, epsg=32643)

    with open(tif_file, "rb") as f:
        inspect_resp = client.post(
            "/api/v1/images/inspect",
            files={"file": ("scene_vqa.tif", f, "image/tiff")},
        )
    assert inspect_resp.status_code == 200
    image_id = inspect_resp.json()["id"]

    # 2. Run VQA
    vqa_resp = client.post(
        "/api/v1/analysis/vqa",
        json={"image_id": image_id, "question": "What land cover types are visible?"},
    )

    assert vqa_resp.status_code == 200
    data = vqa_resp.json()

    assert data["image_id"] == image_id
    assert "answer" in data
    assert "confidence" in data
    assert data["confidence"]["overall"] > 0.0
    assert "evidence" in data
    assert data["evidence"]["id"].startswith("evi_")
    assert len(data["execution_steps"]) >= 3
