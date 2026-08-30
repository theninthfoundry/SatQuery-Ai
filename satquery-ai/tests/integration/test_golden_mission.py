"""Integration test for the Urban Expansion Golden Mission end-to-end."""

import pytest
from pathlib import Path
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from backend.pipelines.golden_mission import run_urban_expansion_golden_mission


def test_urban_expansion_golden_mission_flow():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())

    # Ensure demo bitemporal image records exist
    img1 = db.get(ImageRecord, "img_demo_change_before")
    if not img1:
        img1 = ImageRecord(
            id="img_demo_change_before",
            filename="bitemporal_before_t1.tif",
            path="data/demo/bitemporal_before_t1.tif",
            format="GTiff",
            width=128,
            height=128,
            band_count=3,
            crs="EPSG:32643",
            metadata_json={"transform": [10.0, 0.0, 300000.0, 0.0, -10.0, 2500000.0]},
            is_valid=True,
        )
        db.merge(img1)

    img2 = db.get(ImageRecord, "img_demo_change_after")
    if not img2:
        img2 = ImageRecord(
            id="img_demo_change_after",
            filename="bitemporal_after_t2.tif",
            path="data/demo/bitemporal_after_t2.tif",
            format="GTiff",
            width=128,
            height=128,
            band_count=3,
            crs="EPSG:32643",
            metadata_json={"transform": [10.0, 0.0, 300000.0, 0.0, -10.0, 2500000.0]},
            is_valid=True,
        )
        db.merge(img2)
    db.commit()

    # Ensure files exist on disk
    Path("data/demo").mkdir(parents=True, exist_ok=True)
    if not Path("data/demo/bitemporal_before_t1.tif").exists():
        from scripts.seed_demo_data import seed_demo_scenarios
        seed_demo_scenarios()

    result = run_urban_expansion_golden_mission(
        image_before_id="img_demo_change_before",
        image_after_id="img_demo_change_after",
        query="Has the built-up area increased, where did it occur, and how large was the change?",
        db=db,
    )

    assert "mission_id" in result
    assert "evidence_contract" in result
    assert result["evidence_contract"]["task"] == "urban_expansion_change_detection"
    assert "total_area_m2" in result
    assert "spatial_evidence" in result
    assert len(result["evidence_contract"]["provenance_steps"]) == 5
    print(f"\n✅ Golden Mission Passed: {result['answer']}")
