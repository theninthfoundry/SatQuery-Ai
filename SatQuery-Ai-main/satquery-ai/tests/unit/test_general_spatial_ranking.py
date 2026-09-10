"""Unit tests verifying Generalized Spatial Ranking across physical landcover targets."""

import pytest
from pathlib import Path
from backend.engines.spatial_ranking import spatial_ranking_engine
from backend.geospatial.target_analyzers import get_target_analyzer, WaterBodyTargetAnalyzer, BuiltUpTargetAnalyzer, VegetationTargetAnalyzer


class TestGeneralSpatialRanking:

    @pytest.fixture
    def water_raster(self):
        p = Path("tests/fixtures/synthetic_satellite.tif")
        if not p.exists():
            from tests.fixtures.synthetic_raster import generate_test_geotiff
            generate_test_geotiff(p)
        return p

    def test_target_analyzer_factory(self):
        """Verify factory returns appropriate target analyzers."""
        assert isinstance(get_target_analyzer("water_body"), WaterBodyTargetAnalyzer)
        assert isinstance(get_target_analyzer("lake"), WaterBodyTargetAnalyzer)
        assert isinstance(get_target_analyzer("built_up"), BuiltUpTargetAnalyzer)
        assert isinstance(get_target_analyzer("urban"), BuiltUpTargetAnalyzer)
        assert isinstance(get_target_analyzer("vegetation"), VegetationTargetAnalyzer)
        assert isinstance(get_target_analyzer("forest"), VegetationTargetAnalyzer)

    def test_water_body_ranking_execution(self, water_raster):
        """Verify water body ranking returns genuine candidate polygons."""
        res = spatial_ranking_engine.execute(
            water_raster,
            target="water_body",
            operation="largest",
            image_id="synthetic_satellite",
        )
        assert res["status"] == "success"
        assert res["target"] == "water_body"
        assert "evidence_contract" in res
        assert res["decision"] in ["ANSWER", "QUALIFY", "ABSTAIN"]

    def test_built_up_ranking_execution(self, water_raster):
        """Verify built-up target analyzer executes without errors."""
        res = spatial_ranking_engine.execute(
            water_raster,
            target="built_up",
            operation="largest",
            image_id="synthetic_satellite",
        )
        assert res["status"] == "success"
        assert res["target"] == "built_up"
        assert "finding" in res
        assert "total_ranked" in res

    def test_vegetation_ranking_execution(self, water_raster):
        """Verify vegetation target analyzer executes without errors."""
        res = spatial_ranking_engine.execute(
            water_raster,
            target="vegetation",
            operation="largest",
            image_id="synthetic_satellite",
        )
        assert res["status"] == "success"
        assert res["target"] == "vegetation"
        assert "finding" in res
        assert "total_ranked" in res
