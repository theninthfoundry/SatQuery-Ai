"""Unit tests for WaterBodyAnalyzer statistical ambiguity handling."""

import pytest
import numpy as np
from pathlib import Path

from backend.geospatial.water_body import WaterBodyAnalyzer
from tests.fixtures.synthetic_raster import HAS_RASTERIO

try:
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
except ImportError:
    pass


@pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for geospatial tests")
class TestWaterBodyAmbiguity:

    def test_indistinguishable_lakes_trigger_qualify_decision(self, tmp_path):
        """Verify that two lakes of nearly identical area within mixed-pixel uncertainty output QUALIFY."""
        tif_path = tmp_path / "ambiguous_lakes.tif"
        width, height = 128, 128
        data = np.zeros((4, height, width), dtype=np.uint16)
        # Land base (low Green, high NIR -> NDWI < 0)
        data[0] = 500
        data[1] = 800
        data[2] = 600
        data[3] = 2500

        y_coords, x_coords = np.ogrid[:height, :width]

        # Lake 1: radius approx 15
        mask_1 = (((x_coords - 40) / 15.0) ** 2 + ((y_coords - 40) / 15.0) ** 2) <= 1.0
        # Lake 2: radius approx 15.2 (almost identical size!)
        mask_2 = (((x_coords - 90) / 15.2) ** 2 + ((y_coords - 80) / 15.2) ** 2) <= 1.0

        for m in [mask_1, mask_2]:
            data[0][m] = 1500
            data[1][m] = 1800  # High Green
            data[2][m] = 400
            data[3][m] = 200   # Low NIR -> positive NDWI

        transform = from_origin(500000.0, 3000000.0, 10.0, 10.0)
        crs = CRS.from_epsg(32643)

        with rasterio.open(
            tif_path,
            "w",
            driver="GTiff",
            dtype="uint16",
            count=4,
            width=width,
            height=height,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(data)

        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        res = analyzer.analyze(tif_path)

        assert len(res.candidates) >= 2
        assert res.is_ambiguous_largest is True
        assert res.ambiguity_details is not None
        assert res.ambiguity_details["statistical_status"] == "indistinguishable_at_current_gsd"
        assert res.evidence_decision == "QUALIFY"
        assert "statistically indistinguishable" in res.decision_reason

    def test_distinct_lakes_yield_unambiguous_answer(self, tmp_path):
        """Verify that lakes with clearly separated areas (Δarea >> uncertainty) output confident ANSWER."""
        tif_path = tmp_path / "distinct_lakes.tif"
        width, height = 128, 128
        data = np.zeros((4, height, width), dtype=np.uint16)
        data[0] = 500
        data[1] = 800
        data[2] = 600
        data[3] = 2500

        y_coords, x_coords = np.ogrid[:height, :width]

        # Huge main lake: radius 25
        mask_large = (((x_coords - 50) / 25.0) ** 2 + ((y_coords - 50) / 25.0) ** 2) <= 1.0
        # Tiny pond: radius 6
        mask_small = (((x_coords - 100) / 6.0) ** 2 + ((y_coords - 100) / 6.0) ** 2) <= 1.0

        for m in [mask_large, mask_small]:
            data[0][m] = 1500
            data[1][m] = 1800
            data[2][m] = 400
            data[3][m] = 200

        transform = from_origin(500000.0, 3000000.0, 10.0, 10.0)
        crs = CRS.from_epsg(32643)

        with rasterio.open(
            tif_path,
            "w",
            driver="GTiff",
            dtype="uint16",
            count=4,
            width=width,
            height=height,
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(data)

        analyzer = WaterBodyAnalyzer(min_area_m2=500.0)
        res = analyzer.analyze(tif_path)

        assert len(res.candidates) >= 2
        assert res.is_ambiguous_largest is False
        assert res.evidence_decision == "ANSWER"
