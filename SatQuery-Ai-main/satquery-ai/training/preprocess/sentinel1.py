"""Sentinel-1 SAR radar radiometric calibration and speckle filtering."""

import numpy as np


def apply_lee_filter(radar_img: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Apply Lee adaptive speckle filter to reduce multiplicative radar noise."""
    try:
        from scipy.ndimage import uniform_filter
    except ImportError:
        return radar_img

    mean = uniform_filter(radar_img, (window_size, window_size))
    mean_sq = uniform_filter(radar_img ** 2, (window_size, window_size))
    variance = np.maximum(0.0, mean_sq - mean ** 2)

    overall_var = np.var(radar_img)
    if overall_var <= 1e-6:
        return radar_img

    weights = variance / (variance + overall_var)
    filtered = mean + weights * (radar_img - mean)
    return filtered


def preprocess_sentinel1_grd(
    raw_intensity: np.ndarray,
    to_db: bool = True,
    apply_speckle: bool = True,
    clip_min_db: float = -30.0,
    clip_max_db: float = 5.0,
) -> np.ndarray:
    """Calibrate raw SAR backscatter intensity to decibels (dB) with speckle noise suppression."""
    safe_intensity = np.maximum(raw_intensity.astype(np.float32), 1e-6)

    if to_db:
        # sigma0_db = 10 * log10(intensity)
        sigma0 = 10.0 * np.log10(safe_intensity)
        sigma0 = np.clip(sigma0, clip_min_db, clip_max_db)
    else:
        sigma0 = safe_intensity

    if apply_speckle:
        sigma0 = apply_lee_filter(sigma0, window_size=5)

    return sigma0
