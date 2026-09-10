"""Unit tests for geospatial raster validation."""

from pathlib import Path
from backend.geospatial.validation import validate_file_path, validate_raster_metadata
from backend.geospatial.metadata import extract_raster_metadata
from tests.fixtures.synthetic_raster import (
    create_synthetic_multiband_geotiff,
    create_non_georeferenced_image,
)


def test_validation_valid_geotiff(tmp_path: Path):
    tif_path = tmp_path / "valid.tif"
    create_synthetic_multiband_geotiff(tif_path)

    path_res = validate_file_path(tif_path)
    assert path_res.valid is True
    assert len(path_res.errors) == 0

    meta = extract_raster_metadata(tif_path)
    meta_res = validate_raster_metadata(meta)
    assert meta_res.valid is True
    assert len(meta_res.errors) == 0


def test_validation_missing_crs_warning(tmp_path: Path):
    png_path = tmp_path / "unreferenced.png"
    create_non_georeferenced_image(png_path)

    path_res = validate_file_path(png_path)
    assert path_res.valid is True

    meta = extract_raster_metadata(png_path)
    meta_res = validate_raster_metadata(meta, strict_crs=False)
    assert meta_res.valid is True
    assert len(meta_res.warnings) > 0  # Should warn about lack of CRS
    assert any("CRS" in w for w in meta_res.warnings)


def test_validation_invalid_extension(tmp_path: Path):
    txt_path = tmp_path / "data.txt"
    txt_path.write_text("not an image")

    path_res = validate_file_path(txt_path)
    assert path_res.valid is False
    assert any("Unsupported file format" in e for e in path_res.errors)


def test_validation_non_existent_file(tmp_path: Path):
    path_res = validate_file_path(tmp_path / "ghost.tif")
    assert path_res.valid is False
    assert any("does not exist" in e for e in path_res.errors)
