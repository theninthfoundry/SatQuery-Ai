"""Sentinel-2 multispectral preprocessing and reflectance scaling."""

import numpy as np
from typing import Dict, Any, Tuple


def preprocess_sentinel2_patch(
    raw_array: np.ndarray,
    scale_factor: float = 10000.0,
    clip_min: float = 0.0,
    clip_max: float = 1.0,
) -> np.ndarray:
    """Scale raw Sentinel-2 L2A digital numbers (DN) to surface reflectance [0.0, 1.0].
    
    Args:
        raw_array: [C, H, W] uint16 array of Sentinel-2 bands.
        scale_factor: ESA standard BOA scaling factor (10000.0).
        clip_min: Minimum reflectance boundary.
        clip_max: Maximum reflectance boundary.
        
    Returns:
        float32 array normalized to [clip_min, clip_max].
    """
    scaled = raw_array.astype(np.float32) / scale_factor
    return np.clip(scaled, clip_min, clip_max)


def extract_spectral_indices(s2_tensor: np.ndarray) -> Dict[str, np.ndarray]:
    """Compute standard analytical indices (NDVI, NDWI, MNDWI, NDBI) from normalized S2 tensor.
    
    Assumes standard band order:
    B02 (Blue) = 0, B03 (Green) = 1, B04 (Red) = 2, B08 (NIR) = 3, B11 (SWIR) = 4
    """
    c, h, w = s2_tensor.shape
    green = s2_tensor[1] if c > 1 else s2_tensor[0]
    red = s2_tensor[2] if c > 2 else s2_tensor[0]
    nir = s2_tensor[3] if c > 3 else s2_tensor[0]
    swir = s2_tensor[4] if c > 4 else nir

    eps = 1e-6
    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    mndwi = (green - swir) / (green + swir + eps)
    ndbi = (swir - nir) / (swir + nir + eps)

    return {
        "NDVI": np.clip(ndvi, -1.0, 1.0),
        "NDWI": np.clip(ndwi, -1.0, 1.0),
        "MNDWI": np.clip(mndwi, -1.0, 1.0),
        "NDBI": np.clip(ndbi, -1.0, 1.0),
    }
