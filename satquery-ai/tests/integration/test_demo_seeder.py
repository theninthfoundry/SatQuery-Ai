"""Integration test for Demo Data Seeder and Evaluation Endpoints."""

from fastapi.testclient import TestClient
from backend.main import app
from backend.db import get_db
from backend.models_db import ImageRecord, AOIRecord
from scripts.seed_demo_data import seed_demo_scenarios

client = TestClient(app)


def test_seed_demo_scenarios_and_evaluation_endpoint():
    # 1. Run seeder
    seed_demo_scenarios()

    # 2. Verify seeded DB records
    db = next(get_db())
    aoi = db.get(AOIRecord, "aoi_demo_isro")
    assert aoi is not None
    assert "Ahmedabad" in aoi.name

    img1 = db.get(ImageRecord, "img_demo_optical_1")
    assert img1 is not None
    assert img1.band_count == 4

    img_b = db.get(ImageRecord, "img_demo_bitemporal_t1")
    img_a = db.get(ImageRecord, "img_demo_bitemporal_t2")
    assert img_b is not None and img_a is not None

    img_opt = db.get(ImageRecord, "img_demo_sentinel2_optical")
    img_sar = db.get(ImageRecord, "img_demo_sentinel1_sar")
    assert img_opt is not None and img_sar is not None

    # 3. Test Evaluation Benchmarks List endpoint
    bench_resp = client.get("/api/v1/evaluation/benchmarks")
    assert bench_resp.status_code == 200
    assert len(bench_resp.json()["available_benchmarks"]) == 4

    # 4. Test Evaluation Run endpoint
    run_resp = client.post("/api/v1/evaluation/run")
    assert run_resp.status_code == 200
    assert len(run_resp.json()["benchmarks"]) == 4
