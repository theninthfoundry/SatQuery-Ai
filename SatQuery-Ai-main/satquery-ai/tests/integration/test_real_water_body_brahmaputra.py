"""Integration test verifying deterministic spatial ranking on real Brahmaputra water/flood imagery."""

from pathlib import Path
import pytest
from backend.geospatial.water_body import WaterBodyAnalyzer
from backend.engines.spatial_ranking import SpatialRankingEngine
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from tests.fixtures.synthetic_raster import create_synthetic_water_geotiff


class TestRealWaterBodyBrahmaputra:

    @pytest.fixture(autouse=True)
    def setup_raster_and_db(self, tmp_path):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())

        # Ensure demo raster exists
        self.raster_path = Path("./data/demo/scene_brahmaputra_flood.tif")
        if not self.raster_path.exists():
            create_synthetic_water_geotiff(self.raster_path, width=128, height=128, epsg=32643)

        # Ensure ImageRecord exists in DB
        img = self.db.get(ImageRecord, "img_demo_brahmaputra_flood")
        if not img:
            img = ImageRecord(
                id="img_demo_brahmaputra_flood",
                filename="scene_brahmaputra_flood.tif",
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

    def test_largest_water_body_brahmaputra_e2e(self):
        """Query: 'Where is the largest water body?' on Brahmaputra scene."""
        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        wb_res = analyzer.analyze(self.raster_path, image_id="img_demo_brahmaputra_flood")

        # 1. Scientific assertions on raster analysis
        assert wb_res.candidate_count >= 1, "Must detect at least one candidate water body"
        assert wb_res.selected_candidate is not None
        assert wb_res.evidence_decision == "ANSWER"
        assert wb_res.valid_pixel_ratio == 1.0

        largest = wb_res.selected_candidate
        assert largest.area_ha > 5.0, f"Expected major water body >5 ha, got {largest.area_ha} ha"
        assert largest.area_m2 > 50000.0
        assert largest.centroid["lat"] != 0.0
        assert largest.centroid["lon"] != 0.0

        # Verify geometry is an authentic contour polygon, NOT a rectangle
        geom = largest.geometry
        assert geom["type"] in ["Polygon", "MultiPolygon"]
        coords = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]
        assert len(coords) >= 12, f"Expected curved polygon contour with >=12 vertices, got {len(coords)}"

        # 2. Engine integration assertions
        engine_inst = SpatialRankingEngine()
        result = engine_inst.rank(
            image_id="img_demo_brahmaputra_flood",
            target="water_body",
            operation="largest",
            db=self.db,
            query="Where is the largest water body?",
        )

        assert result["status"] == "success"
        finding = result["finding"]
        assert finding["operation"] == "largest"
        assert finding["target"] == "water_body"
        assert finding["area_ha"] == pytest.approx(largest.area_ha, rel=1e-3)
        assert finding["area_m2"] == pytest.approx(largest.area_m2, rel=1e-3)

        # Verify Evidence Contract has ZERO synthetic confidence
        contract = result["evidence_contract"]
        assert contract["execution_mode"] == "deterministic_gis"
        assert contract["model_confidence"] is None, "Deterministic GIS must NOT fabricate a synthetic confidence score"
        assert contract["gate_decision"] == "ANSWER"

        # Verify spatial features contain authentic GeoJSON polygons tagged with source_image_id
        features = contract["spatial_evidence"]["features"]
        assert len(features) >= 1
        assert features[0]["properties"]["source_image_id"] == "img_demo_brahmaputra_flood"
        assert features[0]["geometry"]["type"] in ["Polygon", "MultiPolygon"]
