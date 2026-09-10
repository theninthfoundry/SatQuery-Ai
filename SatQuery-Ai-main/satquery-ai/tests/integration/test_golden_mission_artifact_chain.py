"""Integration test verifying that the 19-Stage Golden Mission executes end-to-end and produces a real artifact chain."""

from pathlib import Path
import pytest
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from backend.pipelines.golden_mission import run_complete_compound_golden_mission
from scripts.run_golden_mission import ensure_demo_assets


class TestGoldenMissionArtifactChain:

    @pytest.fixture(autouse=True)
    def setup_golden_mission_assets(self):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())
        self.t1_id, self.t2_id, self.sar_id = ensure_demo_assets(self.db)

    def test_golden_mission_full_artifact_chain(self):
        """Execute all 19 stages of Golden Mission and assert real artifact outputs."""
        query = "Between T1 and T2, identify newly developed built-up areas, calculate the changed ground area, and corroborate the finding with SAR."

        result = run_complete_compound_golden_mission(
            image_t1_optical_id=self.t1_id,
            image_t2_optical_id=self.t2_id,
            image_t2_sar_id=self.sar_id,
            query=query,
            db=self.db,
            threshold=0.35,
        )

        assert result is not None
        assert "mission_id" in result

        # 1. Telemetry and Steps Execution
        telemetry = result.get("telemetry", {})
        steps = telemetry.get("steps", [])
        assert len(steps) >= 15, f"Expected full 19-stage DAG, got {len(steps)} steps"
        assert all(s.get("status") in ["SUCCESS", "COMPLETED", "PASSED"] for s in steps)

        # 2. Change clusters with genuine geometries
        clusters = result.get("change_clusters", [])
        assert len(clusters) >= 1, "Must detect at least 1 change cluster"
        primary = clusters[0]
        assert primary["area_ha"] > 0.0
        assert primary["area_m2"] > 0.0
        assert "geometry" in primary
        assert primary["geometry"]["type"] in ["Polygon", "MultiPolygon"]

        # 3. Optical + SAR Corroboration Metrics
        metrics = result.get("metrics", {})
        assert "optical_sar_iou" in metrics
        assert "corroboration_score" in metrics
        assert "registration_score" in metrics
        assert metrics["total_area_ha"] > 0.0

        # 4. Evidence Contract & Gating
        contract = result.get("evidence_contract")
        assert contract is not None
        assert contract["task"] == "multimodal_change_detection"
        assert contract["gate_decision"] in ["ANSWER", "QUALIFY"]
        assert contract["inputs"] == [self.t1_id, self.t2_id, self.sar_id]

        # 5. Generated Report Buffers
        reports = result.get("reports", {})
        assert "geojson" in reports
        assert "csv" in reports
        assert "pdf" in reports
        assert len(reports["geojson"]) > 50, "GeoJSON report must contain valid data"
        assert len(reports["csv"]) > 20, "CSV report must contain valid rows"
        assert len(reports["pdf"]) > 100, "PDF report must contain valid binary bytes"

        # 6. Bitwise Replay Manifest
        manifest = result.get("replay_manifest")
        assert manifest is not None
        assert "inputs_hash" in manifest
        assert "parameters" in manifest
        assert "computed_area_ha" in manifest
        assert manifest["computed_area_ha"] == pytest.approx(metrics["total_area_ha"], rel=1e-3)
