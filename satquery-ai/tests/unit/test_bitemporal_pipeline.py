"""Unit tests for Bi-Temporal Change Detection and Ground Area Calculation."""

import pytest
import numpy as np
from pathlib import Path

from backend.pipelines.bi_temporal import (
    mask_to_geographic_polygons,
    generate_change_mask_overlay,
)


def test_mask_to_geographic_polygons_area():
    # 64x64 mask with a 16x16 center changed box (256 pixels)
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[24:40, 24:40] = 255

    # 10m resolution UTM transform: origin (500000, 3000000)
    transform = [10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0]

    features, total_area_m2 = mask_to_geographic_polygons(
        mask=mask,
        transform=transform,
        width=64,
        height=64,
        epsg=32643,
        min_pixel_area=4,
    )

    assert len(features) == 1
    feat = features[0]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "Polygon"

    # Area of 16x16 pixels at 10m/px = 160m x 160m = 25,600 m²
    # Contour polygon area might be within +- 10% depending on border pixels
    assert 20000.0 <= total_area_m2 <= 30000.0
    assert feat["properties"]["area_ha"] > 2.0


def test_generate_change_mask_overlay(tmp_path: Path):
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[10:30, 10:30] = 255
    out_png = tmp_path / "mask_overlay.png"

    generated = generate_change_mask_overlay(mask, out_png, width=64, height=64)
    assert generated.exists()
    assert generated.stat().st_size > 0
