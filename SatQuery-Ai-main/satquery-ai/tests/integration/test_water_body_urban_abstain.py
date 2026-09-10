"""Integration test verifying that the system honestly ABSTAINS when querying for water on urban imagery."""

from pathlib import Path
import pytest
from backend.geospatial.water_body import WaterBodyAnalyzer
from backend.engines.spatial_ranking import SpatialRankingEngine
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff


class TestWaterBodyUrbanAbstain:

    @pytest.fixture(autouse=True)
    def setup_raster_and_db(self, tmp_path):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())

        self.raster_path = Path("./data/demo/scene_optical_ahmedabad.tif")
        if not self.raster_path.exists():
            create_synthetic_multiband_geotiff(self.raster_path, width=128, height=128, bands=4, epsg=32643)

        img = self.db.get(ImageRecord, "img_demo_optical_1")
        if not img:
            img = ImageRecord(
                id="img_demo_optical_1",
                filename="scene_optical_ahmedabad.tif",
                path=str(self.raster_path),
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

    def test_largest_water_body_urban_abstains_honestly(self):
        """Query: 'Where is the largest water body?' on urban scene with zero water bodies.
        
        A scientifically defensible system must NOT hallucinate a water body just because
        the user asked for one.
        """
        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        wb_res = analyzer.analyze(self.raster_path, image_id="img_demo_optical_1")

        # Must detect zero candidates
        assert wb_res.candidate_count == 0, f"Urban scene should have 0 water bodies, detected {wb_res.candidate_count}"
        assert wb_res.selected_candidate is None
        assert wb_res.total_water_area_m2 == 0.0
        assert wb_res.total_water_area_ha == 0.0
        assert wb_res.evidence_decision == "ABSTAIN"
        assert "No coherent water bodies exceeding the minimum area threshold" in wb_res.decision_reason

        # Engine invocation must also cleanly ABSTAIN
        engine_inst = SpatialRankingEngine()
        result = engine_inst.rank(
            image_id="img_demo_optical_1",
            target="water_body",
            operation="largest",
            db=self.db,
            query="Where is the largest water body?",
        )

        assert result["status"] == "success"
        finding = result["finding"]
        assert finding["candidate_count"] == 0
        assert finding["area_ha"] == 0.0
        assert finding["area_m2"] == 0.0
        assert "No water bodies exceeding the minimum area threshold" in result["answer"]

        contract = result["evidence_contract"]
        assert contract["gate_decision"] == "ABSTAIN"
        assert contract["spatial_evidence"]["features"] == []
        assert contract["model_confidence"] is None
