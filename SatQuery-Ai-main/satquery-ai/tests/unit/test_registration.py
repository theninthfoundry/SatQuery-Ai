"""Unit tests for automated keypoint co-registration and affine warp engine."""

import pytest
import numpy as np
from backend.geospatial.registration import align_image_pairs, _to_gray_uint8


def test_to_gray_uint8():
    rgb = np.ones((50, 50, 3), dtype=np.uint8) * 128
    gray = _to_gray_uint8(rgb)
    assert gray.shape == (50, 50)
    assert gray.dtype == np.uint8
    assert gray[0, 0] == 128


def test_align_identical_image_pairs():
    # Create synthetic textured scene
    np.random.seed(42)
    img_a = np.random.randint(50, 200, size=(100, 100, 3), dtype=np.uint8)
    img_b = img_a.copy()

    aligned_img, score, diag = align_image_pairs(img_a, img_b)
    assert aligned_img is not None
    assert aligned_img.shape == (100, 100, 3)
    assert score >= 0.50
    assert "status" in diag


def test_align_shifted_image_pairs():
    np.random.seed(101)
    # Generate structured synthetic image with shapes
    img_a = np.zeros((200, 200, 3), dtype=np.uint8)
    img_a[40:90, 40:90] = [200, 150, 50]
    img_a[120:170, 120:170] = [50, 200, 150]
    img_a[40:90, 120:170] = [150, 50, 200]

    # Shift Image B by +5 pixels
    img_b = np.roll(img_a, shift=5, axis=(0, 1))

    aligned_img, score, diag = align_image_pairs(img_a, img_b)
    assert aligned_img is not None
    assert aligned_img.shape == (200, 200, 3)
    assert 0.0 <= score <= 1.0


def test_align_handles_none_or_missing_gracefully():
    aligned_img, score, diag = align_image_pairs("non_existent_1.tif", "non_existent_2.tif")
    assert aligned_img is None
    assert score == 0.0
    assert diag["status"] == "FAILED"
