"""Unit tests for CloudQualityEstimator verifying multi-tiered cloud evaluation."""

import pytest
import numpy as np
from pathlib import Path

from backend.geospatial.cloud import CloudQualityEstimator, CloudQualityResult
from tests.fixtures.synthetic_raster import (
    create_synthetic_multiband_geotiff,
    HAS_RASTERIO,
)

try:
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
except ImportError:
    pass


@pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for cloud tests")
class TestCloudQualityEstimator:

    def test_spectral_heuristic_clear_scene(self, tmp_path):
        """Verify that a dark/moderate landscape without clouds evaluates as clear."""
        tif_path = tmp_path / "clear_scene.tif"
        create_synthetic_multiband_geotiff(tif_path, width=64, height=64, bands=4)

        estimator = CloudQualityEstimator()
        res = estimator.estimate(tif_path)

        assert res.valid is True
        assert res.method in ["SPECTRAL_HEURISTIC", "DEFAULT_CLEAR_ASSUMPTION"]
        assert res.cloud_fraction < 0.20
        assert res.quality_flag in ["clear", "acceptable"]

    def test_spectral_heuristic_cloudy_scene(self, tmp_path):
        """Verify that high-albedo cloud pixels trigger cloudy flag and fraction estimation."""
        tif_path = tmp_path / "cloudy_scene.tif"
        width, height = 64, 64
        data = np.zeros((4, height, width), dtype=np.uint16)
        # Moderate terrain base
        data[:] = 800

        # Inject bright cloud in upper half: high RGB and high NIR
        data[:, :32, :] = 8500  # High reflectance ~0.85

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

        estimator = CloudQualityEstimator()
        res = estimator.estimate(tif_path)

        assert res.valid is True
        assert res.method == "SPECTRAL_HEURISTIC"
        # Upper half was set to clouds -> approx 50% cloud fraction
        assert res.cloud_fraction >= 0.40
        assert res.quality_flag in ["degraded", "cloud_contaminated"]
        assert res.cloud_mask is not None
        assert res.cloud_mask.shape == (height, width)

    def test_metadata_tier_cloud_assessment(self, tmp_path):
        """Verify that STAC metadata / raster tags are prioritized when present."""
        tif_path = tmp_path / "meta_scene.tif"
        create_synthetic_multiband_geotiff(tif_path, width=32, height=32, bands=3)

        metadata = {"CLOUD_COVERAGE_ASSESSMENT": "8.3"}

        estimator = CloudQualityEstimator()
        res = estimator.estimate(tif_path, metadata=metadata)

        assert res.valid is True
        assert res.method == "SCENE_METADATA"
        assert abs(res.cloud_fraction - 0.083) < 0.005
        assert res.quality_flag == "acceptable"

    def test_nonexistent_file_handling(self):
        """Verify graceful error reporting when file is missing."""
        estimator = CloudQualityEstimator()
        res = estimator.estimate("non_existent_file.tif")
        assert res.valid is False
        assert res.method == "FILE_NOT_FOUND"
