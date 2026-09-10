"""Integration tests for the Image Inspection endpoint."""

from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_image_inspection_endpoint_geotiff(tmp_path: Path):
    tif_file = tmp_path / "test_satellite.tif"
    create_synthetic_multiband_geotiff(tif_file, width=64, height=64, bands=4, epsg=32643)

    with open(tif_file, "rb") as f:
        response = client.post(
            "/api/v1/images/inspect",
            files={"file": ("test_satellite.tif", f, "image/tiff")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["id"].startswith("img_")
    assert data["status"] == "ready"
    assert data["validation"]["valid"] is True
    assert len(data["validation"]["errors"]) == 0

    # Metadata assertions
    meta = data["metadata"]
    assert meta["width"] == 64
    assert meta["height"] == 64
    assert meta["band_count"] == 4
    assert meta["crs"]["present"] is True
    assert meta["crs"]["epsg"] == 32643
    assert meta["crs"]["type"] == "projected"
    assert len(meta["bands"]) == 4

    # Preview assertion
    assert data["preview"]["available"] is True
    assert data["preview"]["preview_url"] == f"/api/v1/images/{data['id']}/preview"
