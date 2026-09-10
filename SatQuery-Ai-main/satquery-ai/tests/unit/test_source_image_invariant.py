"""Unit tests verifying the hard source-image invariant across the analysis stack."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.engines.spatial_ranking import SpatialRankingEngine
from tests.fixtures.synthetic_raster import (
    create_synthetic_water_geotiff,
    HAS_RASTERIO,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_raster(tmp_path):
    tif_path = tmp_path / "water_invariant.tif"
    create_synthetic_water_geotiff(tif_path, width=64, height=64)
    return str(tif_path)


@pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for geospatial tests")
class TestSourceImageInvariant:

    def test_mismatched_source_image_triggers_analysis_invalid(self, sample_raster):
        """Verify that any mismatch between active image and analysis target raises ANALYSIS_INVALID."""
        engine = SpatialRankingEngine()

        # Submit analysis with active view 'img_hyderabad_2026' but targeting 'img_brahmaputra_flood'
        result = engine.execute(
            image_path=sample_raster,
            target="water_body",
            operation="largest",
            image_id="img_brahmaputra_flood",
            expected_source_image_id="img_hyderabad_2026",
        )

        assert result["status"] == "error"
        assert result["error_code"] == "ANALYSIS_INVALID"
        assert "Source image mismatch" in result["reason"]
        assert result["decision"] == "ABSTAIN"
        # Zero features must be returned to prevent rendering on wrong raster
        assert result["features"] == []
        assert result["pipeline_result"]["features"] == []

    def test_matching_source_image_proceeds_successfully(self, sample_raster):
        """Verify that when active view and target image match, execution proceeds and tags features."""
        engine = SpatialRankingEngine()

        result = engine.execute(
            image_path=sample_raster,
            target="water_body",
            operation="largest",
            image_id="img_brahmaputra_flood",
            expected_source_image_id="img_brahmaputra_flood",
        )

        assert result["status"] == "success"
        assert result["total_ranked"] >= 1
        assert len(result["features"]) >= 1
        # All feature properties must carry verified source_image_id
        for feat in result["features"]:
            assert feat["properties"]["source_image_id"] == "img_brahmaputra_flood"

    def test_api_endpoint_enforces_invariant(self, client, sample_raster):
        """Verify that HTTP API enforces the invariant when expected_source_image_id is provided."""
        payload = {
            "image_path": sample_raster,
            "image_id": "img_raster_A",
            "expected_source_image_id": "img_raster_B",  # Intentional mismatch
            "target": "water_body",
            "operation": "largest",
        }

        response = client.post("/api/v1/analysis/spatial-rank", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "ANALYSIS_INVALID"
        assert data["features"] == []
