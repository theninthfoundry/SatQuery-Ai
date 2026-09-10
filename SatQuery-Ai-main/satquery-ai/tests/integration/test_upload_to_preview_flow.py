"""End-to-end integration test: upload -> inspect -> retrieve preview."""

from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import io

from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_full_upload_to_preview_flow(tmp_path: Path):
    tif_file = tmp_path / "orbit_pass.tif"
    create_synthetic_multiband_geotiff(tif_file, width=80, height=80, bands=4, epsg=32643)

    # 1. Upload & Inspect
    with open(tif_file, "rb") as f:
        inspect_resp = client.post(
            "/api/v1/images/inspect",
            files={"file": ("orbit_pass.tif", f, "image/tiff")},
        )

    assert inspect_resp.status_code == 200
    inspect_data = inspect_resp.json()
    image_id = inspect_data["id"]

    # 2. Fetch preview
    preview_url = inspect_data["preview"]["preview_url"]
    assert preview_url is not None

    preview_resp = client.get(preview_url)
    assert preview_resp.status_code == 200
    assert preview_resp.headers["content-type"] == "image/png"

    # 3. Verify preview bytes form a valid PIL PNG
    preview_img = Image.open(io.BytesIO(preview_resp.content))
    assert preview_img.format == "PNG"
    assert preview_img.width > 0
    assert preview_img.height > 0

    # 4. Fetch metadata directly
    meta_resp = client.get(f"/api/v1/images/{image_id}")
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["id"] == image_id
    assert meta_data["filename"] == "orbit_pass.tif"
