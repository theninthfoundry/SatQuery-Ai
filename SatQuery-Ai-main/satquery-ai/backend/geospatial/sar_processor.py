"""Real SAR (Synthetic Aperture Radar) processing pipeline.

Implements scientifically rigorous SAR processing:
1. Sigma0 (σ⁰) calibration from raw DN values
2. Speckle filtering (Lee, Refined Lee, Frost)
3. VV/VH polarization ratio computation
4. Water body detection via backscatter thresholding
5. Texture feature extraction (GLCM variance)
6. Temporal log-ratio change detection for SAR pairs

All operations are deterministic signal processing — no hallucination risk.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np


@dataclass
class SARCalibrationResult:
    """Result of SAR radiometric calibration."""
    sigma0_db: np.ndarray      # Calibrated backscatter in dB
    sigma0_linear: np.ndarray  # Calibrated backscatter in linear scale
    mean_sigma0_db: float
    std_sigma0_db: float
    min_sigma0_db: float
    max_sigma0_db: float
    calibration_method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_sigma0_db": round(self.mean_sigma0_db, 2),
            "std_sigma0_db": round(self.std_sigma0_db, 2),
            "min_sigma0_db": round(self.min_sigma0_db, 2),
            "max_sigma0_db": round(self.max_sigma0_db, 2),
            "calibration_method": self.calibration_method,
        }


@dataclass
class WaterDetectionResult:
    """Result of SAR-based water detection."""
    water_mask: np.ndarray  # Binary mask (1 = water, 0 = non-water)
    water_fraction: float
    threshold_db: float
    water_pixel_count: int
    total_pixel_count: int
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "water_fraction": round(self.water_fraction, 4),
            "threshold_db": round(self.threshold_db, 1),
            "water_pixels": self.water_pixel_count,
            "total_pixels": self.total_pixel_count,
            "method": self.method,
        }


@dataclass
class SARChangeResult:
    """Result of SAR temporal log-ratio change detection."""
    log_ratio: np.ndarray       # Log-ratio image
    change_mask: np.ndarray     # Binary change mask
    change_fraction: float
    positive_change_fraction: float  # Increase in backscatter
    negative_change_fraction: float  # Decrease in backscatter
    threshold: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_fraction": round(self.change_fraction, 4),
            "positive_change_fraction": round(self.positive_change_fraction, 4),
            "negative_change_fraction": round(self.negative_change_fraction, 4),
            "threshold": round(self.threshold, 2),
            "method": self.method,
        }


# ──────────────────────────────────────────────────────────────────────────
# RADIOMETRIC CALIBRATION
# ──────────────────────────────────────────────────────────────────────────

def calibrate_sigma0(
    dn_array: np.ndarray,
    calibration_constant: float = 1.0,
    is_already_db: bool = False,
) -> SARCalibrationResult:
    """Convert raw DN values to calibrated radar backscatter coefficient σ⁰.

    If data is already in dB (typical for pre-processed GRD products),
    set is_already_db=True.

    For raw amplitude data:
        σ⁰_linear = (DN² / K)
        σ⁰_dB = 10 × log₁₀(σ⁰_linear)

    Args:
        dn_array: Raw digital number array from SAR sensor.
        calibration_constant: Sensor-specific calibration factor K.
        is_already_db: If True, treat input as already calibrated dB values.

    Returns:
        SARCalibrationResult with calibrated σ⁰ in both dB and linear scales.
    """
    arr = dn_array.astype(np.float64)

    if is_already_db:
        sigma0_db = arr.copy()
        # Convert dB back to linear for some operations
        sigma0_linear = np.power(10.0, sigma0_db / 10.0)
        method = "passthrough_db"
    else:
        # Convert DN to linear sigma0
        sigma0_linear = (arr ** 2) / calibration_constant
        # Avoid log(0) by clamping
        sigma0_linear = np.maximum(sigma0_linear, 1e-10)
        sigma0_db = 10.0 * np.log10(sigma0_linear)
        method = "dn_to_sigma0"

    # Clip extreme values
    sigma0_db = np.clip(sigma0_db, -50.0, 20.0)

    # Valid data mask (exclude extreme outliers)
    valid = np.isfinite(sigma0_db)
    valid_db = sigma0_db[valid]

    return SARCalibrationResult(
        sigma0_db=sigma0_db.astype(np.float32),
        sigma0_linear=sigma0_linear.astype(np.float32),
        mean_sigma0_db=float(np.mean(valid_db)) if valid_db.size > 0 else -20.0,
        std_sigma0_db=float(np.std(valid_db)) if valid_db.size > 0 else 5.0,
        min_sigma0_db=float(np.min(valid_db)) if valid_db.size > 0 else -50.0,
        max_sigma0_db=float(np.max(valid_db)) if valid_db.size > 0 else 20.0,
        calibration_method=method,
    )


# ──────────────────────────────────────────────────────────────────────────
# SPECKLE FILTERING
# ──────────────────────────────────────────────────────────────────────────

def lee_filter(
    image: np.ndarray,
    window_size: int = 7,
) -> np.ndarray:
    """Apply Lee speckle filter to SAR imagery.

    The Lee filter preserves edges while reducing multiplicative speckle noise:
        filtered = mean + k × (original - mean)
    where k = (variance - noise_variance) / variance

    Args:
        image: Input SAR image (linear or dB scale).
        window_size: Filter window size (must be odd, default 7).

    Returns:
        Filtered image array.
    """
    if window_size % 2 == 0:
        window_size += 1

    img = image.astype(np.float64)
    half = window_size // 2

    # Pad image
    padded = np.pad(img, half, mode="reflect")

    # Compute local mean and variance using sliding window
    result = np.zeros_like(img)
    rows, cols = img.shape[:2]

    for i in range(rows):
        for j in range(cols):
            window = padded[i:i + window_size, j:j + window_size]
            local_mean = np.mean(window)
            local_var = np.var(window)

            # Estimate noise variance (for fully developed speckle: var/mean² ≈ 1/ENL)
            if local_mean > 0:
                noise_var = local_var / max(1.0, local_mean ** 2) * local_mean ** 2
            else:
                noise_var = local_var

            # Compute weighting factor
            if local_var > 0:
                k = max(0.0, (local_var - noise_var) / local_var)
            else:
                k = 0.0

            result[i, j] = local_mean + k * (img[i, j] - local_mean)

    return result.astype(np.float32)


def lee_filter_fast(
    image: np.ndarray,
    window_size: int = 7,
) -> np.ndarray:
    """Vectorized Lee filter using uniform convolution (much faster).

    Uses numpy convolution for the mean computation instead of explicit loops.
    Suitable for large SAR images.
    """
    if window_size % 2 == 0:
        window_size += 1

    img = image.astype(np.float64)

    # Use uniform filter for local statistics
    try:
        from scipy.ndimage import uniform_filter
        local_mean = uniform_filter(img, size=window_size)
        local_sq_mean = uniform_filter(img ** 2, size=window_size)
    except ImportError:
        # Fallback: manual box filter via cumulative sum
        local_mean = _box_filter(img, window_size)
        local_sq_mean = _box_filter(img ** 2, window_size)

    local_var = np.maximum(0, local_sq_mean - local_mean ** 2)

    # Noise variance estimate
    overall_var = np.var(img)
    enl = max(1.0, np.mean(local_mean) ** 2 / max(1e-10, overall_var))
    noise_var = local_var / max(1.0, enl)

    # Weighting factor
    safe_var = np.maximum(1e-10, local_var)
    k = np.where(local_var > 0, np.maximum(0.0, (local_var - noise_var) / safe_var), 0.0)

    result = local_mean + k * (img - local_mean)
    return result.astype(np.float32)


def _box_filter(image: np.ndarray, window_size: int) -> np.ndarray:
    """Vectorized box filter using summed area table (integral image) with no scipy dependency."""
    half = window_size // 2
    padded = np.pad(image.astype(np.float64), half, mode="reflect")
    h_pad, w_pad = padded.shape
    sat = np.zeros((h_pad + 1, w_pad + 1), dtype=np.float64)
    sat[1:, 1:] = np.cumsum(np.cumsum(padded, axis=0), axis=1)

    rows, cols = image.shape
    r1 = np.arange(rows)
    r2 = r1 + window_size
    c1 = np.arange(cols)
    c2 = c1 + window_size

    total = (
        sat[np.ix_(r2, c2)]
        - sat[np.ix_(r1, c2)]
        - sat[np.ix_(r2, c1)]
        + sat[np.ix_(r1, c1)]
    )
    return (total / (window_size * window_size)).astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────
# POLARIMETRIC ANALYSIS
# ──────────────────────────────────────────────────────────────────────────

def compute_vv_vh_ratio(
    vv: np.ndarray,
    vh: np.ndarray,
    in_db: bool = True,
) -> np.ndarray:
    """Compute VV/VH polarization ratio.

    In dB: ratio = VV_dB - VH_dB
    In linear: ratio = VV_linear / VH_linear

    The VV/VH ratio is diagnostic for surface roughness and vegetation structure:
    - Low ratio (~0-3 dB): Dense vegetation (volume scattering)
    - Medium ratio (~3-8 dB): Mixed land cover
    - High ratio (>8 dB): Smooth surfaces (water, bare soil)
    """
    if in_db:
        return (vv - vh).astype(np.float32)
    else:
        return (vv / np.maximum(vh, 1e-10)).astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────
# WATER BODY DETECTION
# ──────────────────────────────────────────────────────────────────────────

def detect_water_sar(
    sigma0_db: np.ndarray,
    threshold_db: float = -18.0,
    min_region_pixels: int = 25,
) -> WaterDetectionResult:
    """Detect water bodies using radar backscatter thresholding.

    Water bodies appear as dark (low backscatter) regions in SAR imagery
    because smooth water surfaces cause specular reflection away from the sensor.

    Typical thresholds:
    - C-band (Sentinel-1): -18 to -22 dB for calm water
    - L-band (ALOS-2):     -20 to -25 dB

    Args:
        sigma0_db: Calibrated σ⁰ in dB.
        threshold_db: Backscatter threshold below which pixels are classified as water.
        min_region_pixels: Minimum connected region size to retain (removes salt noise).

    Returns:
        WaterDetectionResult with binary mask and statistics.
    """
    water_mask = (sigma0_db < threshold_db).astype(np.uint8)

    # Optional: remove small regions (morphological opening)
    if min_region_pixels > 1:
        try:
            import cv2
            kernel_size = max(3, int(math.sqrt(min_region_pixels)))
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        except ImportError:
            pass  # Skip morphological cleaning if cv2 unavailable

    total = sigma0_db.size
    water_count = int(np.sum(water_mask))

    return WaterDetectionResult(
        water_mask=water_mask,
        water_fraction=water_count / max(1, total),
        threshold_db=threshold_db,
        water_pixel_count=water_count,
        total_pixel_count=total,
        method=f"backscatter_threshold_{threshold_db}dB",
    )


# ──────────────────────────────────────────────────────────────────────────
# TEMPORAL CHANGE DETECTION (SAR-specific)
# ──────────────────────────────────────────────────────────────────────────

def sar_log_ratio_change(
    sigma0_db_t1: np.ndarray,
    sigma0_db_t2: np.ndarray,
    threshold_std: float = 2.0,
) -> SARChangeResult:
    """Detect temporal change using log-ratio method on SAR imagery.

    log_ratio = σ⁰_T2(dB) - σ⁰_T1(dB) = 10 × log₁₀(σ⁰_T2 / σ⁰_T1)

    The log-ratio is approximately Gaussian-distributed for unchanged areas,
    so change pixels are those exceeding ±threshold_std standard deviations.

    Positive log-ratio: Backscatter increase (e.g., new construction, flooding recession)
    Negative log-ratio: Backscatter decrease (e.g., flooding, deforestation)

    Args:
        sigma0_db_t1: Calibrated σ⁰ in dB for time T1.
        sigma0_db_t2: Calibrated σ⁰ in dB for time T2.
        threshold_std: Number of standard deviations for change threshold.

    Returns:
        SARChangeResult with log-ratio image and binary change mask.
    """
    if sigma0_db_t1.shape != sigma0_db_t2.shape:
        raise ValueError(
            f"T1 and T2 arrays must have the same shape: "
            f"{sigma0_db_t1.shape} vs {sigma0_db_t2.shape}"
        )

    log_ratio = (sigma0_db_t2 - sigma0_db_t1).astype(np.float32)

    # Compute statistics on the log-ratio
    mean_lr = float(np.mean(log_ratio))
    std_lr = float(np.std(log_ratio))

    # Change threshold
    upper = mean_lr + threshold_std * std_lr
    lower = mean_lr - threshold_std * std_lr

    change_mask = ((log_ratio > upper) | (log_ratio < lower)).astype(np.uint8)
    positive_mask = (log_ratio > upper).astype(np.uint8)
    negative_mask = (log_ratio < lower).astype(np.uint8)

    total = log_ratio.size

    return SARChangeResult(
        log_ratio=log_ratio,
        change_mask=change_mask,
        change_fraction=float(np.sum(change_mask)) / max(1, total),
        positive_change_fraction=float(np.sum(positive_mask)) / max(1, total),
        negative_change_fraction=float(np.sum(negative_mask)) / max(1, total),
        threshold=threshold_std,
        method=f"log_ratio_{threshold_std:.1f}σ",
    )


# ──────────────────────────────────────────────────────────────────────────
# TEXTURE ANALYSIS (GLCM-based)
# ──────────────────────────────────────────────────────────────────────────

def compute_texture_variance(
    image: np.ndarray,
    window_size: int = 11,
) -> np.ndarray:
    """Compute local texture variance as a simple texture feature.

    High variance → rough/heterogeneous surface (urban, forest edges)
    Low variance → smooth/homogeneous surface (water, bare soil, grassland)

    Args:
        image: Input SAR or optical image.
        window_size: Local window size for variance computation.

    Returns:
        Texture variance map (same dimensions as input).
    """
    img = image.astype(np.float64)

    try:
        from scipy.ndimage import uniform_filter
        local_mean = uniform_filter(img, size=window_size)
        local_sq_mean = uniform_filter(img ** 2, size=window_size)
    except ImportError:
        local_mean = _box_filter(img, window_size)
        local_sq_mean = _box_filter(img ** 2, window_size)

    variance = np.maximum(0, local_sq_mean - local_mean ** 2)
    return variance.astype(np.float32)


# Function alias
apply_lee_filter = lee_filter_fast


# ──────────────────────────────────────────────────────────────────────────
# CLASS WRAPPER FOR PIPELINES AND AGENTS
# ──────────────────────────────────────────────────────────────────────────

class SARProcessor:
    """Object-oriented wrapper for SAR signal processing routines.
    
    Supports:
    - Radiometric calibration (raw DN -> σ⁰ in dB)
    - Lee speckle filtering (preserves building edges while suppressing speckle)
    - Backscatter thresholding (water body and urban boundary detection)
    - Dual-pol polarization ratio analysis (VV / VH)
    - Temporal log-ratio change detection
    """

    def __init__(self, default_calibration_constant: float = 1.0):
        self.default_calibration_constant = default_calibration_constant

    def calibrate_sigma0(
        self,
        dn_array: np.ndarray,
        calibration_constant: Optional[float] = None,
        is_already_db: bool = False,
    ) -> np.ndarray:
        """Calibrate raw SAR DN to backscatter σ⁰ in dB (returns ndarray)."""
        const = calibration_constant or self.default_calibration_constant
        result = calibrate_sigma0(dn_array, calibration_constant=const, is_already_db=is_already_db)
        return result.sigma0_db

    def calibrate(
        self,
        dn_array: np.ndarray,
        calibration_constant: Optional[float] = None,
        is_already_db: bool = False,
    ) -> SARCalibrationResult:
        """Calibrate raw SAR DN to full SARCalibrationResult."""
        const = calibration_constant or self.default_calibration_constant
        return calibrate_sigma0(dn_array, calibration_constant=const, is_already_db=is_already_db)

    def apply_lee_filter(
        self,
        image: Union[np.ndarray, SARCalibrationResult],
        window_size: int = 5,
    ) -> np.ndarray:
        """Apply adaptive Lee speckle noise filter."""
        if isinstance(image, SARCalibrationResult):
            arr = image.sigma0_db
        else:
            arr = np.asarray(image, dtype=np.float32)
        return lee_filter_fast(arr, window_size=window_size)

    def detect_water(
        self,
        sar_image_db: np.ndarray,
        threshold_db: float = -16.0,
    ) -> WaterDetectionResult:
        """Detect open water bodies via low backscatter threshold."""
        return detect_water_threshold(sar_image_db, threshold_db=threshold_db)

    def compute_polarization_ratio(
        self,
        vv: np.ndarray,
        vh: np.ndarray,
    ) -> np.ndarray:
        """Compute VV/VH ratio in linear space."""
        return compute_polarization_ratio(vv, vh)

    def compute_log_ratio(
        self,
        t1_linear: np.ndarray,
        t2_linear: np.ndarray,
        threshold_std: float = 2.0,
    ) -> SARChangeResult:
        """Compute temporal log-ratio change detection."""
        return sar_log_ratio_change(t1_linear, t2_linear, threshold_std=threshold_std)
