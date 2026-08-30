"""Unit tests for CRS detection and validation."""

import pytest
from backend.geospatial.crs import inspect_crs

try:
    import rasterio.crs
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


def test_crs_detection_projected_epsg():
    crs_info = inspect_crs("EPSG:32643")
    assert crs_info.present is True
    assert crs_info.valid is True
    assert crs_info.epsg == 32643
    assert crs_info.crs_type == "projected"
    assert crs_info.status == "ok"


def test_crs_detection_geographic_epsg():
    crs_info = inspect_crs("EPSG:4326")
    assert crs_info.present is True
    assert crs_info.valid is True
    assert crs_info.epsg == 4326
    assert crs_info.crs_type == "geographic"
    assert crs_info.status == "ok"


def test_crs_detection_missing():
    crs_info = inspect_crs(None)
    assert crs_info.present is False
    assert crs_info.valid is False
    assert crs_info.epsg is None
    assert crs_info.crs_type == "missing"
    assert crs_info.status == "warning"


@pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for rasterio.crs.CRS test")
def test_crs_detection_rasterio_crs():
    crs = CRS.from_epsg(3857)
    crs_info = inspect_crs(crs)
    assert crs_info.present is True
    assert crs_info.epsg == 3857
    assert crs_info.crs_type == "projected"
