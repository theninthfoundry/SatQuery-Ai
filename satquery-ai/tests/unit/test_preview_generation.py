"""Unit tests for raster preview generation."""

from pathlib import Path
from PIL import Image
import numpy as np

from backend.storage.preview import generate_raster_preview, normalize_band_to_uint8
from tests.fixtures.synthetic_raster import (
    create_synthetic_multiband_geotiff,
    create_synthetic_singleband_geotiff,
    create_non_georeferenced_image,
)


def test_preview_generation_multiband(tmp_path: Path):
    tif_path = tmp_path / "multiband.tif"
    out_png = tmp_path / "preview.png"
    create_synthetic_multiband_geotiff(tif_path, width=128, height=128, bands=4)

    generated = generate_raster_preview(tif_path, out_png, max_dimension=256)
    assert generated.exists()
    assert generated.stat().st_size > 0

    # Verify preview is a valid image readable by PIL
    with Image.open(generated) as img:
        assert img.format == "PNG"
        assert img.size[0] <= 256
        assert img.size[1] <= 256


def test_preview_generation_singleband(tmp_path: Path):
    tif_path = tmp_path / "singleband.tif"
    out_png = tmp_path / "single_preview.png"
    create_synthetic_singleband_geotiff(tif_path, width=64, height=64)

    generated = generate_raster_preview(tif_path, out_png)
    assert generated.exists()

    with Image.open(generated) as img:
        assert img.format == "PNG"
        assert img.mode in ("L", "RGB", "RGBA")


def test_normalize_band_to_uint8():
    arr = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=np.float32)
    norm = normalize_band_to_uint8(arr)
    assert norm.dtype == np.uint8
    assert norm.shape == (2, 2)
    assert norm.min() >= 0
    assert norm.max() <= 255
