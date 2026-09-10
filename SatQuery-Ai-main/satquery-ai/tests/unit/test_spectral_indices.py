"""Unit tests for multi-spectral indices (NDVI, NDWI, NDBI) and SAR backscatter sigma0 calculations."""

import pytest
import numpy as np
from backend.geospatial.raster import (
    compute_ndvi,
    compute_ndwi,
    compute_ndbi,
    compute_sar_backscatter_sigma0,
)


def test_compute_ndvi():
    # Dense vegetation: NIR is high, Red is low
    red = np.array([[20, 30], [25, 35]], dtype=np.float32)
    nir = np.array([[180, 200], [170, 190]], dtype=np.float32)

    ndvi = compute_ndvi(red, nir)
    assert ndvi.shape == (2, 2)
    # NDVI should be > 0.6 for dense vegetation
    assert np.all(ndvi > 0.6)
    assert np.all(ndvi <= 1.0)


def test_compute_ndwi():
    # Water: Green is high, NIR is low (strong absorption)
    green = np.array([[150, 140], [160, 155]], dtype=np.float32)
    nir = np.array([[20, 15], [25, 18]], dtype=np.float32)

    ndwi = compute_ndwi(green, nir)
    assert ndwi.shape == (2, 2)
    # NDWI should be > 0.5 for water bodies
    assert np.all(ndwi > 0.5)


def test_compute_ndbi():
    # Built-up / Urban: SWIR is high, NIR is moderate
    swir = np.array([[180, 200], [175, 195]], dtype=np.float32)
    nir = np.array([[90, 100], [85, 95]], dtype=np.float32)

    ndbi = compute_ndbi(swir, nir)
    assert ndbi.shape == (2, 2)
    assert np.all(ndbi > 0.2)


def test_compute_sar_backscatter_sigma0():
    # Linear intensity array
    intensity = np.array([[0.001, 0.05], [0.5, 2.0]], dtype=np.float32)
    sigma0_db = compute_sar_backscatter_sigma0(intensity)

    assert sigma0_db.shape == (2, 2)
    # 0.001 -> -30 dB (water)
    assert sigma0_db[0, 0] < -20.0
    # 0.05 -> -13 dB (soil/vegetation)
    assert -20.0 < sigma0_db[0, 1] < -5.0
    # 2.0 -> +3 dB (urban double-bounce)
    assert sigma0_db[1, 1] > 0.0


def test_division_by_zero_guard():
    # Test all-zero inputs
    zeros = np.zeros((10, 10), dtype=np.float32)
    ndvi = compute_ndvi(zeros, zeros)
    assert np.all(np.isfinite(ndvi))
    assert np.all(ndvi == 0.0)

    ndwi = compute_ndwi(zeros, zeros)
    assert np.all(np.isfinite(ndwi))
