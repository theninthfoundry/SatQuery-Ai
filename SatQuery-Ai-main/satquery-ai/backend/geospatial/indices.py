"""Deterministic spectral index calculator for multispectral satellite imagery.

Implements standard remote sensing vegetation, water, and built-up indices
using physically-grounded band arithmetic. All outputs are deterministic —
no neural networks, no learned parameters, no hallucination risk.

Supported indices:
- NDVI (Normalized Difference Vegetation Index)
- NDWI (Normalized Difference Water Index, McFeeters 1996)
- MNDWI (Modified NDWI, Xu 2006)
- NDBI (Normalized Difference Built-up Index)
- NDMI (Normalized Difference Moisture Index)
- SAVI (Soil-Adjusted Vegetation Index)
- EVI (Enhanced Vegetation Index)
- BSI (Bare Soil Index)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np


@dataclass
class IndexResult:
    """Result of a spectral index computation."""
    name: str
    full_name: str
    formula: str
    array: np.ndarray  # 2D float32 array, values typically in [-1, 1]
    min_val: float
    max_val: float
    mean_val: float
    std_val: float
    valid_pixel_count: int
    total_pixel_count: int
    nodata_fraction: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata (not the array) for JSON output."""
        return {
            "name": self.name,
            "full_name": self.full_name,
            "formula": self.formula,
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "mean": round(self.mean_val, 4),
            "std": round(self.std_val, 4),
            "valid_pixels": self.valid_pixel_count,
            "total_pixels": self.total_pixel_count,
            "nodata_fraction": round(self.nodata_fraction, 4),
        }


def _safe_normalized_diff(
    a: np.ndarray,
    b: np.ndarray,
    nodata_val: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute (a - b) / (a + b) safely, handling division by zero and nodata.

    Returns:
        Tuple of (index_array, valid_mask)
    """
    a = a.astype(np.float32)
    b = b.astype(np.float32)

    # Build valid mask
    valid = np.ones(a.shape, dtype=bool)
    if nodata_val is not None:
        valid &= (a != nodata_val) & (b != nodata_val)

    denominator = a + b
    # Avoid division by zero
    zero_mask = np.abs(denominator) < 1e-10
    denominator[zero_mask] = 1.0  # Prevent div/0; result will be masked

    result = (a - b) / denominator
    result[zero_mask] = 0.0
    result[~valid] = 0.0

    # Clip to [-1, 1] (physical range for normalized differences)
    result = np.clip(result, -1.0, 1.0)

    valid &= ~zero_mask

    return result, valid


def _make_index_result(
    name: str,
    full_name: str,
    formula: str,
    array: np.ndarray,
    valid_mask: np.ndarray,
) -> IndexResult:
    """Create an IndexResult from computed array and validity mask."""
    total = array.size
    valid_count = int(np.sum(valid_mask))
    valid_data = array[valid_mask]

    return IndexResult(
        name=name,
        full_name=full_name,
        formula=formula,
        array=array,
        min_val=float(np.min(valid_data)) if valid_count > 0 else 0.0,
        max_val=float(np.max(valid_data)) if valid_count > 0 else 0.0,
        mean_val=float(np.mean(valid_data)) if valid_count > 0 else 0.0,
        std_val=float(np.std(valid_data)) if valid_count > 0 else 0.0,
        valid_pixel_count=valid_count,
        total_pixel_count=total,
        nodata_fraction=1.0 - valid_count / max(1, total),
    )


# ──────────────────────────────────────────────────────────────────────────
# VEGETATION INDICES
# ──────────────────────────────────────────────────────────────────────────

def compute_ndvi(
    nir: np.ndarray,
    red: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Normalized Difference Vegetation Index.

    NDVI = (NIR - Red) / (NIR + Red)

    Values:
        -1.0 to 0.0: Water, bare soil, clouds, snow
        0.0 to 0.2:  Sparse vegetation, urban
        0.2 to 0.5:  Moderate vegetation
        0.5 to 1.0:  Dense, healthy vegetation

    Args:
        nir: Near-Infrared band array (e.g., Sentinel-2 B08, Landsat B5)
        red: Red band array (e.g., Sentinel-2 B04, Landsat B4)
    """
    result, valid = _safe_normalized_diff(nir, red, nodata_val)
    return _make_index_result(
        name="NDVI",
        full_name="Normalized Difference Vegetation Index",
        formula="(NIR - Red) / (NIR + Red)",
        array=result,
        valid_mask=valid,
    )


def compute_evi(
    nir: np.ndarray,
    red: np.ndarray,
    blue: np.ndarray,
    gain: float = 2.5,
    c1: float = 6.0,
    c2: float = 7.5,
    l: float = 1.0,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Enhanced Vegetation Index.

    EVI = G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)

    More sensitive than NDVI in dense canopy areas (reduces atmospheric
    and soil background influences).

    Args:
        nir: Near-Infrared band
        red: Red band
        blue: Blue band
        gain: Gain factor (default 2.5)
        c1: Atmospheric correction coefficient for red (default 6.0)
        c2: Atmospheric correction coefficient for blue (default 7.5)
        l: Canopy background adjustment (default 1.0)
    """
    nir_f = nir.astype(np.float32)
    red_f = red.astype(np.float32)
    blue_f = blue.astype(np.float32)

    valid = np.ones(nir_f.shape, dtype=bool)
    if nodata_val is not None:
        valid &= (nir_f != nodata_val) & (red_f != nodata_val) & (blue_f != nodata_val)

    denom = nir_f + c1 * red_f - c2 * blue_f + l
    zero_mask = np.abs(denom) < 1e-10
    denom[zero_mask] = 1.0

    result = gain * (nir_f - red_f) / denom
    result[zero_mask] = 0.0
    result[~valid] = 0.0
    result = np.clip(result, -1.0, 1.0)
    valid &= ~zero_mask

    return _make_index_result(
        name="EVI",
        full_name="Enhanced Vegetation Index",
        formula="G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)",
        array=result,
        valid_mask=valid,
    )


def compute_savi(
    nir: np.ndarray,
    red: np.ndarray,
    l_factor: float = 0.5,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Soil-Adjusted Vegetation Index.

    SAVI = ((NIR - Red) / (NIR + Red + L)) × (1 + L)

    Reduces soil brightness influence in areas with sparse vegetation.

    Args:
        nir: Near-Infrared band
        red: Red band
        l_factor: Soil brightness correction (0=dense, 1=sparse; default 0.5)
    """
    nir_f = nir.astype(np.float32)
    red_f = red.astype(np.float32)

    valid = np.ones(nir_f.shape, dtype=bool)
    if nodata_val is not None:
        valid &= (nir_f != nodata_val) & (red_f != nodata_val)

    denom = nir_f + red_f + l_factor
    zero_mask = np.abs(denom) < 1e-10
    denom[zero_mask] = 1.0

    result = ((nir_f - red_f) / denom) * (1.0 + l_factor)
    result[zero_mask] = 0.0
    result[~valid] = 0.0
    result = np.clip(result, -1.0, 1.0)
    valid &= ~zero_mask

    return _make_index_result(
        name="SAVI",
        full_name="Soil-Adjusted Vegetation Index",
        formula="((NIR - Red) / (NIR + Red + L)) × (1 + L)",
        array=result,
        valid_mask=valid,
    )


# ──────────────────────────────────────────────────────────────────────────
# WATER INDICES
# ──────────────────────────────────────────────────────────────────────────

def compute_ndwi(
    green: np.ndarray,
    nir: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Normalized Difference Water Index (McFeeters 1996).

    NDWI = (Green - NIR) / (Green + NIR)

    Values:
        > 0.0: Water bodies
        < 0.0: Vegetation, soil, built-up

    Args:
        green: Green band (e.g., Sentinel-2 B03, Landsat B3)
        nir: Near-Infrared band
    """
    result, valid = _safe_normalized_diff(green, nir, nodata_val)
    return _make_index_result(
        name="NDWI",
        full_name="Normalized Difference Water Index (McFeeters)",
        formula="(Green - NIR) / (Green + NIR)",
        array=result,
        valid_mask=valid,
    )


def compute_mndwi(
    green: np.ndarray,
    swir: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Modified NDWI (Xu 2006).

    MNDWI = (Green - SWIR) / (Green + SWIR)

    Preferred over NDWI for suppressing built-up area noise.

    Args:
        green: Green band
        swir: SWIR band (e.g., Sentinel-2 B11, Landsat B6)
    """
    result, valid = _safe_normalized_diff(green, swir, nodata_val)
    return _make_index_result(
        name="MNDWI",
        full_name="Modified Normalized Difference Water Index (Xu 2006)",
        formula="(Green - SWIR) / (Green + SWIR)",
        array=result,
        valid_mask=valid,
    )


# ──────────────────────────────────────────────────────────────────────────
# BUILT-UP & SOIL INDICES
# ──────────────────────────────────────────────────────────────────────────

def compute_ndbi(
    swir: np.ndarray,
    nir: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Normalized Difference Built-up Index.

    NDBI = (SWIR - NIR) / (SWIR + NIR)

    Values:
        > 0.0: Built-up areas
        < 0.0: Non-built-up (vegetation, water)

    Args:
        swir: SWIR band (e.g., Sentinel-2 B11)
        nir: Near-Infrared band
    """
    result, valid = _safe_normalized_diff(swir, nir, nodata_val)
    return _make_index_result(
        name="NDBI",
        full_name="Normalized Difference Built-up Index",
        formula="(SWIR - NIR) / (SWIR + NIR)",
        array=result,
        valid_mask=valid,
    )


def compute_ndmi(
    nir: np.ndarray,
    swir: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Normalized Difference Moisture Index.

    NDMI = (NIR - SWIR) / (NIR + SWIR)

    Sensitive to vegetation water content. Used for drought monitoring.

    Args:
        nir: Near-Infrared band
        swir: SWIR band (e.g., Sentinel-2 B11)
    """
    result, valid = _safe_normalized_diff(nir, swir, nodata_val)
    return _make_index_result(
        name="NDMI",
        full_name="Normalized Difference Moisture Index",
        formula="(NIR - SWIR) / (NIR + SWIR)",
        array=result,
        valid_mask=valid,
    )


def compute_bsi(
    blue: np.ndarray,
    red: np.ndarray,
    nir: np.ndarray,
    swir: np.ndarray,
    nodata_val: Optional[float] = None,
) -> IndexResult:
    """Compute Bare Soil Index.

    BSI = ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))

    Highlights bare soil, denuded areas, and exposed rock.

    Args:
        blue: Blue band
        red: Red band
        nir: Near-Infrared band
        swir: SWIR band
    """
    a = swir.astype(np.float32) + red.astype(np.float32)
    b = nir.astype(np.float32) + blue.astype(np.float32)
    result, valid = _safe_normalized_diff(a, b, nodata_val=None)

    # Apply nodata masking if needed
    if nodata_val is not None:
        nodata_mask = (
            (blue == nodata_val) | (red == nodata_val) |
            (nir == nodata_val) | (swir == nodata_val)
        )
        result[nodata_mask] = 0.0
        valid &= ~nodata_mask

    return _make_index_result(
        name="BSI",
        full_name="Bare Soil Index",
        formula="((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))",
        array=result,
        valid_mask=valid,
    )


# ──────────────────────────────────────────────────────────────────────────
# CHANGE INDICES (for bi-temporal analysis)
# ──────────────────────────────────────────────────────────────────────────

def compute_delta_index(
    index_t1: IndexResult,
    index_t2: IndexResult,
) -> IndexResult:
    """Compute temporal difference (ΔIndex = T2 - T1) between two spectral indices.

    Positive values indicate increase in the index at T2.
    Negative values indicate decrease.

    Useful for: ΔNDVI (vegetation loss/gain), ΔNDBI (urbanization),
    ΔNDWI (water expansion/recession).
    """
    if index_t1.array.shape != index_t2.array.shape:
        raise ValueError(
            f"Array shapes must match: T1 is {index_t1.array.shape}, "
            f"T2 is {index_t2.array.shape}"
        )

    delta = index_t2.array - index_t1.array
    valid = np.ones(delta.shape, dtype=bool)
    delta_name = f"Δ{index_t1.name}"

    return _make_index_result(
        name=delta_name,
        full_name=f"Temporal Difference ({index_t1.full_name})",
        formula=f"{index_t1.name}(T2) - {index_t1.name}(T1)",
        array=delta,
        valid_mask=valid,
    )
