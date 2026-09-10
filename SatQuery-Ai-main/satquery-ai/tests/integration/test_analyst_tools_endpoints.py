"""Integration tests for Analyst Tools endpoints: AOI upload, Pixel Inspector, Zonal Stats, and Timeline."""

from pathlib import Path
import json
from fastapi.testclient import TestClient

from backend.main import app
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff

client = TestClient(app)


def test_aoi_upload_and_observations(tmp_path: Path):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [78.40, 17.40],
                            [78.45, 17.40],
                            [78.45, 17.45],
                            [78.40, 17.45],
                            [78.40, 17.40],
                        ]
                    ],
                },
                "properties": {"name": "Hyderabad AOI"},
            }
        ],
    }
    content = json.dumps(geojson_data).encode("utf-8")

    # 1. Upload AOI
    resp = client.post(
        "/api/v1/aoi/upload",
        files={"file": ("hyderabad.geojson", content, "application/geo+json")},
        data={"name": "Hyderabad Zone 1"},
    )
    assert resp.status_code == 200
    aoi_data = resp.json()
    assert aoi_data["name"] == "Hyderabad Zone 1"
    assert aoi_data["area_ha"] > 0
    assert aoi_data["perimeter_m"] > 0
    aoi_id = aoi_data["id"]

    # 2. Get AOI observations
    obs_resp = client.get(f"/api/v1/aoi/{aoi_id}/observations")
    assert obs_resp.status_code == 200
    obs_data = obs_resp.json()
    assert "aoi" in obs_data
    assert "observations" in obs_data


def test_timeline_endpoint():
    resp = client.get("/api/v1/images/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)


def test_pixel_inspect_and_zonal_stats(tmp_path: Path):
    # Ingest synthetic image T1
    tif_1 = tmp_path / "t1_opt.tif"
    create_synthetic_multiband_geotiff(tif_1, width=64, height=64, bands=4, epsg=4326)
    with open(tif_1, "rb") as f:
        r1 = client.post("/api/v1/images/inspect", files={"file": ("t1_opt.tif", f, "image/tiff")})
    assert r1.status_code == 200
    img1_id = r1.json()["id"]

    # Ingest synthetic image T2
    tif_2 = tmp_path / "t2_opt.tif"
    create_synthetic_multiband_geotiff(tif_2, width=64, height=64, bands=4, epsg=4326)
    with open(tif_2, "rb") as f:
        r2 = client.post("/api/v1/images/inspect", files={"file": ("t2_opt.tif", f, "image/tiff")})
    assert r2.status_code == 200
    img2_id = r2.json()["id"]

    bounds = r1.json()["metadata"]["bounds"]["wgs84"]
    center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2.0
    center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2.0

    # 1. Pixel Inspect with comparison
    inspect_resp = client.post(
        f"/api/v1/images/{img1_id}/pixel-inspect",
        json={
            "lat": center_lat,
            "lon": center_lon,
            "compare_image_id": img2_id,
        },
    )
    assert inspect_resp.status_code == 200
    pdata = inspect_resp.json()
    assert pdata["in_bounds"] is True
    assert pdata["status"] == "ok"
    assert "bands" in pdata
    assert "indices" in pdata
    assert "comparison" in pdata
    assert pdata["comparison"]["t2_image_id"] == img2_id

    # 2. Zonal Stats
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [bounds["min_lon"], bounds["min_lat"]],
                [bounds["max_lon"], bounds["min_lat"]],
                [bounds["max_lon"], bounds["max_lat"]],
                [bounds["min_lon"], bounds["max_lat"]],
                [bounds["min_lon"], bounds["min_lat"]],
            ]
        ],
    }
    zonal_resp = client.post(
        f"/api/v1/images/{img1_id}/zonal-stats",
        json={"geometry": poly, "band_index": 1},
    )
    assert zonal_resp.status_code == 200
    zdata = zonal_resp.json()
    assert zdata["count"] > 0
    assert "mean" in zdata
    assert "std" in zdata
    assert "median" in zdata
    assert "p95" in zdata
