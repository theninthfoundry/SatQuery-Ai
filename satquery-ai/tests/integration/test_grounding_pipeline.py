"""Integration test for Visual Grounding endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_grounding_pipeline_endpoint(tmp_path: Path):
    # 1. Ingest image
    tif_file = tmp_path / "scene_grounding.tif"
    create_synthetic_multiband_geotiff(tif_file, width=64, height=64, bands=4, epsg=32643)

    with open(tif_file, "rb") as f:
        inspect_resp = client.post(
            "/api/v1/images/inspect",
            files={"file": ("scene_grounding.tif", f, "image/tiff")},
        )
    assert inspect_resp.status_code == 200
    image_id = inspect_resp.json()["id"]

    # 2. Run Grounding
    ground_resp = client.post(
        "/api/v1/analysis/grounding",
        json={"image_id": image_id, "referring_expression": "Highlight the water body"},
    )

    assert ground_resp.status_code == 200
    data = ground_resp.json()

    assert data["image_id"] == image_id
    assert data["referring_expression"] == "Highlight the water body"
    assert "regions_geojson" in data
    assert data["regions_geojson"]["type"] == "FeatureCollection"
    assert len(data["regions_geojson"]["features"]) > 0

    # Validate feature geometry
    feat = data["regions_geojson"]["features"][0]
    assert feat["geometry"]["type"] == "Polygon"
    assert "area_m2" in feat["properties"]
    assert feat["properties"]["area_m2"] > 0

    # Validate evidence
    assert "evidence" in data
    assert data["evidence"]["output_geometry"] is not None
    assert data["confidence"]["overall"] > 0.0
