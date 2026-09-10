"""Unit tests for WaterBodyAnalyzer and spatial ranking calculations."""

import pytest
from pathlib import Path
import numpy as np

from backend.geospatial.water_body import WaterBodyAnalyzer, WaterBodyCandidate
from tests.fixtures.synthetic_raster import (
    create_synthetic_water_geotiff,
    create_synthetic_multiband_geotiff,
    HAS_RASTERIO,
)


@pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for geospatial tests")
class TestWaterBodyAnalyzer:

    def test_detect_two_water_bodies_ranks_correctly(self, tmp_path):
        """Verify that WaterBodyAnalyzer detects both water bodies and accurately ranks the largest."""
        tif_path = tmp_path / "synthetic_water.tif"
        create_synthetic_water_geotiff(tif_path, width=128, height=128)

        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        candidates, summary = analyzer.analyze(tif_path)

        assert summary["status"] == "success"
        assert len(candidates) >= 2, f"Expected at least 2 water bodies, found {len(candidates)}"

        largest = candidates[0]
        second = candidates[1]

        # Verify ranking order by physical area
        assert largest.is_largest is True
        assert largest.rank == 1
        assert second.is_largest is False
        assert second.rank == 2
        assert largest.area_m2 > second.area_m2
        assert largest.area_ha > second.area_ha

        # Verify genuine GeoJSON Polygon geometry
        assert largest.geojson_polygon is not None
        assert largest.geojson_polygon["type"] == "Polygon"
        coords = largest.geojson_polygon["coordinates"]
        assert len(coords) >= 1
        assert len(coords[0]) >= 4  # Closed ring with at least 4 vertices

        # Verify coordinates are in WGS84 geographic range
        for lon, lat in coords[0]:
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0

        # Verify centroid is inside reasonable bounds
        assert -180.0 <= largest.centroid_lon <= 180.0
        assert -90.0 <= largest.centroid_lat <= 90.0

    def test_dry_scene_detects_no_water(self, tmp_path):
        """Verify that a scene without water yields 0 candidates and clean status."""
        tif_path = tmp_path / "dry_land.tif"
        # Standard multiband has gradient values without high Green / low NIR water signature
        create_synthetic_multiband_geotiff(tif_path, width=64, height=64, bands=4)

        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        candidates, summary = analyzer.analyze(tif_path)

        assert candidates == []
        assert summary["status"] == "no_water_detected"
        assert summary["candidates_count"] == 0

    def test_filter_small_noise(self, tmp_path):
        """Verify that water bodies smaller than min_area_m2 threshold are excluded."""
        tif_path = tmp_path / "synthetic_water.tif"
        create_synthetic_water_geotiff(tif_path, width=128, height=128)

        # Set min_area_m2 very high to exclude the smaller pond
        analyzer = WaterBodyAnalyzer(min_area_m2=100000.0)
        candidates, _ = analyzer.analyze(tif_path)

        # All candidates must strictly satisfy the area threshold
        for c in candidates:
            assert c.area_m2 >= 100000.0
