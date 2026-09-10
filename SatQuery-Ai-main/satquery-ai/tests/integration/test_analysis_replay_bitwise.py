"""Integration test verifying bitwise analysis replay and reproduction difference detection."""

from pathlib import Path
import pytest
from backend.db import get_db, Base, engine
from scripts.reproduce_analysis import reproduce_analysis
from scripts.run_golden_mission import ensure_demo_assets


class TestAnalysisReplayBitwise:

    @pytest.fixture(autouse=True)
    def setup_demo_and_db(self):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())
        ensure_demo_assets(self.db)

    def test_bitwise_replay_of_golden_analysis(self):
        """Replay an analysis and verify that all scientific checks pass."""
        report = reproduce_analysis("golden")

        assert report is not None
        assert report["status"] in ["REPRODUCED", "SUCCESS"]

        checks = report["checks"]
        assert checks["inputs"] == "PASSED", "Input raster hashes must match"
        assert checks["parameters"] == "PASSED", "Analytical parameters must match"
        assert checks["geometry"] == "PASSED", "Vector polygon geometries must match"
        assert checks["metrics"] == "PASSED", "Physical ground metrics must match"

        # Verify area match
        comp = report.get("comparison", {})
        if comp.get("original_area_ha") is not None and comp.get("reproduced_area_ha") is not None:
            assert abs(float(comp["original_area_ha"]) - float(comp["reproduced_area_ha"])) < 0.05
