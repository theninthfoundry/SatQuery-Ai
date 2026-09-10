"""Unit tests for EarthObservationAsset, InputSanitizer, and CompatibilityEngine."""

import pytest
import numpy as np
from pathlib import Path
from backend.assets import (
    EarthObservationAsset,
    InputSanitizer,
    CompatibilityEngine,
    AssetFactory,
)
from backend.assets.descriptor import Modality, SpatialResolution, BoundingBox


def test_input_sanitizer_path_traversal():
    sanitizer = InputSanitizer()
    res = sanitizer.sanitize("../hostile.tif")
    assert not res.safe
    assert any("traversal" in e.lower() or "not exist" in e.lower() for e in res.errors)


def test_compatibility_engine_spatial_overlap():
    asset1 = EarthObservationAsset(
        id="a1",
        path=Path("dummy1.tif"),
        filename="dummy1.tif",
        checksum="abc",
        width=1000,
        height=1000,
        crs="EPSG:4326",
        epsg=4326,
        bounds=BoundingBox(min_x=77.0, min_y=12.0, max_x=78.0, max_y=13.0),
        resolution=SpatialResolution(x_res=0.0001, y_res=0.0001, units="degree"),
        transform=[0.0001, 0, 77.0, 0, -0.0001, 13.0],
        georeferenced=True,
        band_count=3,
        bands=[],
        dtype="uint8",
        modality=Modality.OPTICAL,
    )

    # Identical bounds -> 1.0 overlap
    asset2 = EarthObservationAsset(
        id="a2",
        path=Path("dummy2.tif"),
        filename="dummy2.tif",
        checksum="def",
        width=1000,
        height=1000,
        crs="EPSG:4326",
        epsg=4326,
        bounds=BoundingBox(min_x=77.0, min_y=12.0, max_x=78.0, max_y=13.0),
        resolution=SpatialResolution(x_res=0.0001, y_res=0.0001, units="degree"),
        transform=[0.0001, 0, 77.0, 0, -0.0001, 13.0],
        georeferenced=True,
        band_count=3,
        bands=[],
        dtype="uint8",
        modality=Modality.OPTICAL,
    )

    engine = CompatibilityEngine()
    report = engine.check_compatibility(asset1, asset2)
    assert report.compatible
    assert report.spatial_overlap == 1.0
    assert report.crs_same


def test_compatibility_engine_disjoint_rejection():
    asset1 = EarthObservationAsset(
        id="a1",
        path=Path("dummy1.tif"),
        filename="dummy1.tif",
        checksum="abc",
        width=1000,
        height=1000,
        crs="EPSG:4326",
        epsg=4326,
        bounds=BoundingBox(min_x=10.0, min_y=10.0, max_x=11.0, max_y=11.0),
        resolution=SpatialResolution(x_res=0.0001, y_res=0.0001, units="degree"),
        transform=[],
        georeferenced=True,
        band_count=3,
        bands=[],
        dtype="uint8",
        modality=Modality.OPTICAL,
    )
    asset2 = EarthObservationAsset(
        id="a2",
        path=Path("dummy2.tif"),
        filename="dummy2.tif",
        checksum="def",
        width=1000,
        height=1000,
        crs="EPSG:4326",
        epsg=4326,
        bounds=BoundingBox(min_x=50.0, min_y=50.0, max_x=51.0, max_y=51.0),
        resolution=SpatialResolution(x_res=0.0001, y_res=0.0001, units="degree"),
        transform=[],
        georeferenced=True,
        band_count=3,
        bands=[],
        dtype="uint8",
        modality=Modality.OPTICAL,
    )

    engine = CompatibilityEngine()
    report = engine.check_compatibility(asset1, asset2)
    assert not report.compatible
    assert report.spatial_overlap == 0.0
    assert any("spatial overlap" in e.lower() for e in report.errors)
