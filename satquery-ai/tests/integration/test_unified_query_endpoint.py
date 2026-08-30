"""Integration tests for Unified Agent Query endpoint and Report Downloads."""

from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_unified_query_and_reports(tmp_path: Path):
    # 1. Ingest image
    tif_file = tmp_path / "scene_query.tif"
    create_synthetic_multiband_geotiff(tif_file, width=64, height=64, bands=4, epsg=32643)

    with open(tif_file, "rb") as f:
        inspect_resp = client.post(
            "/api/v1/images/inspect",
            files={"file": ("scene_query.tif", f, "image/tiff")},
        )
    assert inspect_resp.status_code == 200
    img_id = inspect_resp.json()["id"]

    # 2. Query Agent with VQA question
    query_resp = client.post(
        "/api/v1/query",
        json={
            "query": "What land cover types are visible?",
            "image_ids": [img_id],
        },
    )
    assert query_resp.status_code == 200
    data = query_resp.json()

    assert data["intent"] == "vqa"
    assert "answer" in data
    assert "job_id" in data
    assert "report_urls" in data
    job_id = data["job_id"]

    # 3. Test PDF Download
    pdf_resp = client.get(f"/api/v1/reports/{job_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"

    # 4. Test GeoJSON Download
    geojson_resp = client.get(f"/api/v1/reports/{job_id}/geojson")
    assert geojson_resp.status_code == 200
    assert "type" in geojson_resp.json()

    # 5. Test CSV Download
    csv_resp = client.get(f"/api/v1/reports/{job_id}/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
