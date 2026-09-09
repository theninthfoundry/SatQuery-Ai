import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from backend.geospatial.water_detector import (
    BandSet,
    Capability,
    detect_water_bodies,
    rank_candidates,
)


def make_synthetic_scene(size=200, radius=30, gsd_m=10.0, seed=0):
    """
    Build a synthetic 'lake in a field' scene:
      - Green band: mid reflectance everywhere, low over water
      - SWIR band: mid reflectance everywhere, very low over water (water
        absorbs SWIR strongly -> MNDWI = (Green-SWIR)/(Green+SWIR) is high
        over water)
    """
    rng = np.random.default_rng(seed)
    green = (0.20 + rng.normal(0, 0.01, (size, size))).astype(np.float32)
    swir = (0.25 + rng.normal(0, 0.01, (size, size))).astype(np.float32)

    yy, xx = np.mgrid[0:size, 0:size]
    cy, cx = size // 2, size // 2
    circle_mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= radius ** 2

    green[circle_mask] = 0.08 + rng.normal(0, 0.005, circle_mask.sum())
    swir[circle_mask] = 0.02 + rng.normal(0, 0.005, circle_mask.sum())

    true_pixel_area = int(circle_mask.sum())
    true_area_m2 = true_pixel_area * (gsd_m ** 2)
    return green, swir, true_area_m2, true_pixel_area


def test_detects_synthetic_lake_with_reasonable_area():
    green, swir, true_area_m2, _ = make_synthetic_scene()
    bands = BandSet(green=green, swir=swir)
    result = detect_water_bodies(bands, gsd_m=10.0)

    assert result.capability == Capability.FULL
    assert result.index_used == "MNDWI"
    assert result.largest is not None

    detected_area = result.largest.area_m2
    # allow generous tolerance: Otsu threshold + morphology will erode edges somewhat
    rel_error = abs(detected_area - true_area_m2) / true_area_m2
    assert rel_error < 0.35, f"area off by {rel_error:.1%}: detected={detected_area}, true={true_area_m2}"
    assert result.largest.area_method == "pixel_grid_approx"  # no pyproj/shapely in this sandbox


def test_prefers_mndwi_over_ndwi_when_swir_available():
    green, swir, _, _ = make_synthetic_scene()
    nir = green.copy()  # irrelevant content; presence alone shouldn't override SWIR preference
    bands = BandSet(green=green, swir=swir, nir=nir)
    result = detect_water_bodies(bands, gsd_m=10.0)
    assert result.index_used == "MNDWI"


def test_falls_back_to_ndwi_without_swir():
    green, swir, _, _ = make_synthetic_scene()
    # reuse swir array as a stand-in "nir" band just to exercise the NDWI path
    bands = BandSet(green=green, nir=swir)
    result = detect_water_bodies(bands, gsd_m=10.0)
    assert result.index_used == "NDWI"
    assert any("NDWI" in n for n in result.limitation_notes)


def test_capability_degrades_on_unknown_bands():
    """This is the audit's 'Critical correction': never fake NDWI on RGB
    imagery with unknown band semantics."""
    r = np.random.default_rng(0).random((50, 50)).astype(np.float32)
    b = np.random.default_rng(1).random((50, 50)).astype(np.float32)
    unlabeled_bands = BandSet(green=None, swir=None, nir=None, red=r)
    result = detect_water_bodies(unlabeled_bands, gsd_m=10.0)

    assert result.capability == Capability.LIMITED
    assert result.index_used is None
    assert result.candidates == []
    assert any("Refusing to compute a water index" in n for n in result.limitation_notes)


def test_cloud_mask_excludes_contaminated_pixels():
    green, swir, _, _ = make_synthetic_scene()
    cloud_mask = np.zeros_like(green, dtype=bool)
    cloud_mask[:, :] = True  # entire scene "clouded"
    bands = BandSet(green=green, swir=swir, cloud_mask=cloud_mask)
    result = detect_water_bodies(bands, gsd_m=10.0)
    # everything masked out -> LIMITED, not a fabricated detection
    assert result.capability == Capability.LIMITED
    assert result.candidates == []


def test_ranking_largest_vs_smallest():
    size = 300
    rng = np.random.default_rng(2)
    green = (0.20 + rng.normal(0, 0.01, (size, size))).astype(np.float32)
    swir = (0.25 + rng.normal(0, 0.01, (size, size))).astype(np.float32)

    for (cy, cx, r) in [(60, 60, 25), (220, 220, 12)]:
        yy, xx = np.mgrid[0:size, 0:size]
        m = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
        green[m] = 0.08
        swir[m] = 0.02

    bands = BandSet(green=green, swir=swir)
    result = detect_water_bodies(bands, gsd_m=10.0, min_pixel_area=10)
    assert len(result.candidates) >= 2

    largest = rank_candidates(result, operation="largest")[0]
    smallest = rank_candidates(result, operation="smallest")[0]
    assert largest.area_m2 > smallest.area_m2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
