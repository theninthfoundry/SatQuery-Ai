"""Unit tests for raster metadata extraction."""

import pytest
from pathlib import Path
from backend.geospatial.metadata import extract_raster_metadata
from tests.fixtures.synthetic_raster import (
    create_synthetic_multiband_geotiff,
    create_non_georeferenced_image,
)


def test_raster_metadata_multiband_geotiff(tmp_path: Path):
    tif_path = tmp_path / "synthetic_utm.tif"
    create_synthetic_multiband_geotiff(
        tif_path,
        width=128,
        height=96,
        bands=4,
        epsg=32643,
        resolution=10.0,
    )

    meta = extract_raster_metadata(tif_path)

    assert meta.filename == "synthetic_utm.tif"
    assert meta.format == "GeoTIFF"
    assert meta.width == 128
    assert meta.height == 96
    assert meta.band_count == 4
    assert meta.dtype == "uint16"
    assert meta.crs.present is True
    assert meta.crs.epsg == 32643
    assert meta.crs.crs_type == "projected"
    assert meta.resolution.x_res == 10.0
    assert meta.resolution.y_res == 10.0
    assert meta.bounds is not None
    assert meta.bounds.min_x == 500000.0
    assert len(meta.bands) == 4

    # Verify per-band stats
    for idx, b in enumerate(meta.bands, start=1):
        assert b.band_index == idx
        assert b.min > 0
        assert b.max >= b.min
        assert b.mean > 0


def test_raster_metadata_non_georeferenced(tmp_path: Path):
    png_path = tmp_path / "sample.png"
    create_non_georeferenced_image(png_path, width=64, height=48)

    meta = extract_raster_metadata(png_path)

    assert meta.filename == "sample.png"
    assert meta.width == 64
    assert meta.height == 48
    assert meta.band_count == 3
    assert meta.crs.present is False
    assert meta.crs.status == "warning"
