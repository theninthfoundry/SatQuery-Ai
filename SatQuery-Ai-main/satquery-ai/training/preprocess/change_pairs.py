"""Bi-temporal image pair synchronization and data augmentation."""

import numpy as np
from typing import Tuple


def prepare_bitemporal_pair(
    img_t1: np.ndarray,
    img_t2: np.ndarray,
    target_size: Tuple[int, int] = (256, 256),
) -> Tuple[np.ndarray, np.ndarray]:
    """Ensure identical spatial dimensions and normalized reflectance for T1 and T2."""
    c1, h1, w1 = img_t1.shape
    c2, h2, w2 = img_t2.shape

    # Crop to shared minimum bounding box
    min_h = min(h1, h2, target_size[0])
    min_w = min(w1, w2, target_size[1])

    t1_crop = img_t1[:, :min_h, :min_w].astype(np.float32)
    t2_crop = img_t2[:, :min_h, :min_w].astype(np.float32)

    # Normalize each channel to [0, 1]
    for c in range(min(c1, c2)):
        denom1 = np.ptp(t1_crop[c]) or 1.0
        denom2 = np.ptp(t2_crop[c]) or 1.0
        t1_crop[c] = (t1_crop[c] - np.min(t1_crop[c])) / denom1
        t2_crop[c] = (t2_crop[c] - np.min(t2_crop[c])) / denom2

    return t1_crop, t2_crop


def paired_augmentation(
    t1: np.ndarray,
    t2: np.ndarray,
    mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply identical spatial geometric transformations (flips and 90-deg rotations) to both dates."""
    # Random horizontal flip
    if np.random.rand() > 0.5:
        t1 = np.flip(t1, axis=-1).copy()
        t2 = np.flip(t2, axis=-1).copy()
        mask = np.flip(mask, axis=-1).copy()

    # Random vertical flip
    if np.random.rand() > 0.5:
        t1 = np.flip(t1, axis=-2).copy()
        t2 = np.flip(t2, axis=-2).copy()
        mask = np.flip(mask, axis=-2).copy()

    # Random 90-degree rotation
    k = np.random.randint(0, 4)
    if k > 0:
        t1 = np.rot90(t1, k, axes=(-2, -1)).copy()
        t2 = np.rot90(t2, k, axes=(-2, -1)).copy()
        mask = np.rot90(mask, k, axes=(-2, -1)).copy()

    return t1, t2, mask
