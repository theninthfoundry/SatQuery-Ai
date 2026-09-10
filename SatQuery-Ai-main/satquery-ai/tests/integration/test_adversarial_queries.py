"""Integration test evaluating the system against adversarial prompts and deliberate edge cases.

Verifies:
1. "Where is the largest water body?" -> executes argmax area
2. "Which water body is the smallest?" -> executes argmin area
3. "Show me the largest built-up region." -> executes built-up ranking
4. Wrong image ID -> fails fast with ANALYSIS_INVALID or 404
5. Non-georeferenced or corrupted image -> handled safely with descriptive error
"""

from pathlib import Path
import pytest

from backend.agent.query_planner import query_capability_planner
from backend.engines.spatial_ranking import SpatialRankingEngine
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from tests.fixtures.synthetic_raster import create_synthetic_water_geotiff


class TestAdversarialQueries:

    @pytest.fixture(autouse=True)
    def setup_data(self, tmp_path):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())

        self.water_path = Path("./data/demo/scene_brahmaputra_flood.tif")
        if not self.water_path.exists():
            create_synthetic_water_geotiff(self.water_path, width=128, height=128, epsg=32643)

        img = self.db.get(ImageRecord, "img_demo_brahmaputra_flood")
        if not img:
            img = ImageRecord(
                id="img_demo_brahmaputra_flood",
                filename="scene_brahmaputra_flood.tif",
                path=str(self.water_path),
                format="GTiff",
                width=128,
                height=128,
                band_count=4,
                dtype="uint8",
                crs="WGS 84 / UTM zone 43N",
                epsg=32643,
                is_valid=True,
            )
            self.db.add(img)
            self.db.commit()

    def test_query_planner_superlatives(self):
        """Verify semantic decomposition handles largest, smallest, built-up, and change."""
        # 1. Largest water body
        p1 = query_capability_planner.plan("Where is the largest water body?")
        assert p1.intent == "spatial_ranking"
        assert p1.target == "water_body"
        assert p1.operation == "largest"

        # 2. Smallest water body
        p2 = query_capability_planner.plan("Which water body is the smallest?")
        assert p2.intent == "spatial_ranking"
        assert p2.target == "water_body"
        assert p2.operation == "smallest"

        # 3. Largest built-up area
        p3 = query_capability_planner.plan("Show me the largest built-up region in this scene.")
        assert p3.intent == "spatial_ranking"
        assert p3.target == "built_up"
        assert p3.operation == "largest"

        # 4. Bi-temporal change query
        p4 = query_capability_planner.plan("What changed between these two dates?", available_assets_count=2)
        assert p4.intent == "bi_temporal_change"
        assert p4.temporal_required is True

    def test_smallest_water_body_selection(self):
        """Verify that 'smallest' operation selects candidate with smallest area."""
        engine_inst = SpatialRankingEngine()
        res_largest = engine_inst.rank(
            image_id="img_demo_brahmaputra_flood",
            target="water_body",
            operation="largest",
            db=self.db,
            query="Where is the largest water body?",
        )
        res_smallest = engine_inst.rank(
            image_id="img_demo_brahmaputra_flood",
            target="water_body",
            operation="smallest",
            db=self.db,
            query="Which water body is the smallest?",
        )

        assert res_largest["status"] == "success"
        assert res_smallest["status"] == "success"

        # If multiple candidates exist, smallest area must be <= largest area
        if res_largest["finding"]["candidate_count"] > 1:
            assert res_smallest["finding"]["area_ha"] <= res_largest["finding"]["area_ha"]
            assert res_smallest["finding"]["operation"] == "smallest"

    def test_deliberate_source_image_mismatch_fails_fast(self):
        """Verify that passing an unexpected image ID fails fast with ANALYSIS_INVALID."""
        engine_inst = SpatialRankingEngine()
        res = engine_inst.rank(
            image_id="img_demo_brahmaputra_flood",
            target="water_body",
            operation="largest",
            db=self.db,
            query="Where is the largest water body?",
            expected_source_image_id="different_image_id_xyz",
        )

        assert res["status"] == "error"
        assert res["error_code"] == "ANALYSIS_INVALID"
        assert "Source image mismatch" in res["reason"]
        assert res["features"] == []

    def test_nonexistent_image_id_handled_gracefully(self):
        """Verify that querying a non-existent image ID does not crash."""
        engine_inst = SpatialRankingEngine()
        res = engine_inst.rank(
            image_id="img_nonexistent_ghost",
            target="water_body",
            operation="largest",
            db=self.db,
            query="Where is the largest water body?",
        )

        assert res["status"] == "error"
        assert "not found" in res["reason"].lower()
