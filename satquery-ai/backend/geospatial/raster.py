"""Raster reading, windowed sampling, statistics, and conservative modality classification."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import rasterio
    from rasterio.windows import Window
    from rasterio.enums import ColorInterp
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:  # pragma: no cover
    HAS_PIL = False


@dataclass
class BandStatistics:
    band_index: int
    dtype: str
    min: float
    max: float
    mean: float
    std: Optional[float] = None
    nodata: Optional[float] = None


@dataclass
class ModalityDetection:
    modality: str  # "optical", "multispectral", "sar", "unknown"
    confidence: float
    basis: List[str] = field(default_factory=list)


def compute_band_stats(
    dataset_or_array: Any,
    band_idx: int = 1,
    nodata_val: Optional[float] = None,
    max_sample_pixels: int = 1_000_000,
) -> BandStatistics:
    """Compute min, max, mean, and std for a band safely using sampling for large arrays."""
    if HAS_RASTERIO and hasattr(dataset_or_array, "read"):
        ds = dataset_or_array
        width, height = ds.width, ds.height
        total_pixels = width * height

        # If image is very large, read decimation / overview or sample windows
        if total_pixels > max_sample_pixels:
            step = int(np.ceil(np.sqrt(total_pixels / max_sample_pixels)))
            data = ds.read(band_idx, out_shape=(1, max(1, height // step), max(1, width // step)))
        else:
            data = ds.read(band_idx)

        dtype_str = ds.dtypes[band_idx - 1]
    elif isinstance(dataset_or_array, np.ndarray):
        data = dataset_or_array
        dtype_str = str(data.dtype)
    else:
        raise ValueError("Unsupported data input for compute_band_stats")

    # Filter invalid and nodata values
    arr = np.asarray(data).astype(np.float64)
    valid_mask = np.isfinite(arr)
    if nodata_val is not None:
        valid_mask &= (arr != nodata_val)

    valid_data = arr[valid_mask]
    if valid_data.size == 0:
        return BandStatistics(
            band_index=band_idx,
            dtype=dtype_str,
            min=0.0,
            max=0.0,
            mean=0.0,
            std=0.0,
            nodata=nodata_val,
        )

    b_min = float(np.min(valid_data))
    b_max = float(np.max(valid_data))
    b_mean = float(np.mean(valid_data))
    b_std = float(np.std(valid_data))

    return BandStatistics(
        band_index=band_idx,
        dtype=dtype_str,
        min=round(b_min, 4),
        max=round(b_max, 4),
        mean=round(b_mean, 4),
        std=round(b_std, 4),
        nodata=nodata_val,
    )


def detect_modality(
    band_count: int,
    filename: str,
    color_interps: Optional[List[Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    band_stats: Optional[List[BandStatistics]] = None,
) -> ModalityDetection:
    """Conservatively detect image modality.
    
    Returns 'unknown' with 0.0 confidence when evidence is insufficient.
    Never claims 'SAR' solely because band_count is 1.
    """
    tags = tags or {}
    lower_fn = filename.lower()
    basis: List[str] = []

    # 1. Check explicit tags / descriptions
    tag_blob = " ".join([f"{k}:{v}" for k, v in tags.items()]).lower()
    if any(k in tag_blob for k in ["sentinel-1", "sar", "backscatter", "grd", "slc", "pol:vv", "pol:vh"]):
        basis.append("Raster metadata contains explicit SAR/Sentinel-1 tags")
        return ModalityDetection(modality="sar", confidence=0.95, basis=basis)

    if any(k in tag_blob for k in ["sentinel-2", "landsat", "multispectral", "planetscope"]):
        basis.append("Raster metadata contains explicit optical/multispectral tags")
        return ModalityDetection(modality="multispectral", confidence=0.95, basis=basis)

    # 2. Check filename hints
    if any(k in lower_fn for k in ["_sar", "-sar", "s1_", "sentinel1", "backscatter"]):
        basis.append(f"Filename '{filename}' indicates SAR sensor")
        return ModalityDetection(modality="sar", confidence=0.85, basis=basis)

    if any(k in lower_fn for k in ["_opt", "-opt", "s2_", "sentinel2", "landsat", "rgb", "optical"]):
        if band_count > 3:
            basis.append(f"Filename '{filename}' and band count ({band_count}) indicate multispectral imagery")
            return ModalityDetection(modality="multispectral", confidence=0.85, basis=basis)
        else:
            basis.append(f"Filename '{filename}' indicates optical imagery")
            return ModalityDetection(modality="optical", confidence=0.85, basis=basis)

    # 3. Check color interpretations
    if color_interps and len(color_interps) >= 3:
        if HAS_RASTERIO:
            ci_names = [ci.name.lower() if hasattr(ci, "name") else str(ci).lower() for ci in color_interps]
            if "red" in ci_names and "green" in ci_names and "blue" in ci_names:
                basis.append("Color interpretation defines explicit Red, Green, Blue bands")
                return ModalityDetection(modality="optical", confidence=0.9, basis=basis)

    # 4. Standard optical/multispectral defaults with moderate confidence
    if band_count in (3, 4) and ("red" in lower_fn or "green" in lower_fn or "blue" in lower_fn):
        basis.append(f"Band count ({band_count}) and spectral band naming in file")
        return ModalityDetection(modality="optical", confidence=0.8, basis=basis)

    if band_count > 4:
        basis.append(f"High band count ({band_count}) suggests multispectral/hyperspectral imagery")
        return ModalityDetection(modality="multispectral", confidence=0.7, basis=basis)

    if band_count == 3:
        basis.append(f"Standard 3-band structure without SAR tags (likely RGB optical)")
        return ModalityDetection(modality="optical", confidence=0.6, basis=basis)

    # 5. Single band without explicit SAR indicator -> strictly unknown
    if band_count == 1:
        basis.append("Single band raster without explicit sensor or modality tags")
        return ModalityDetection(modality="unknown", confidence=0.0, basis=basis)

    return ModalityDetection(modality="unknown", confidence=0.0, basis=["Insufficient modality metadata"])


def compute_ndvi(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Vegetation Index (NDVI = (NIR - Red) / (NIR + Red)).
    
    Values range from -1.0 to +1.0:
    - Dense healthy vegetation: > 0.5
    - Sparse vegetation / shrubs: 0.2 - 0.5
    - Bare soil: 0.0 - 0.2
    - Water / Cloud: < 0.0
    """
    red = red_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = nir + red
    # Guard against division by zero
    ndvi = np.where(denominator > 1e-6, (nir - red) / denominator, 0.0)
    return np.clip(ndvi, -1.0, 1.0)


def compute_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """Calculate McFeeters Normalized Difference Water Index (NDWI = (Green - NIR) / (Green + NIR)).
    
    Values range from -1.0 to +1.0:
    - Open water bodies / flood inundation: > 0.0
    - Non-water (soil, vegetation, urban): <= 0.0
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    ndwi = np.where(denominator > 1e-6, (green - nir) / denominator, -1.0)
    return np.clip(ndwi, -1.0, 1.0)


def compute_ndbi(swir_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Built-up Index (NDBI = (SWIR - NIR) / (SWIR + NIR)).
    
    Values range from -1.0 to +1.0:
    - Built-up urban surfaces: > 0.0
    - Vegetation / water: < 0.0
    """
    swir = swir_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = swir + nir
    ndbi = np.where(denominator > 1e-6, (swir - nir) / denominator, -1.0)
    return np.clip(ndbi, -1.0, 1.0)


def compute_sar_backscatter_sigma0(
    intensity: np.ndarray,
    calibration_constant_db: float = 0.0,
) -> np.ndarray:
    """Convert raw linear SAR intensity or DN into calibrated backscatter sigma0 (σ⁰ in dB).
    
    σ⁰ (dB) = 10 * log10(intensity + 1e-10) + calibration_constant
    - Calm water / specular reflection: < -22 dB
    - Smooth soil / airport runways: -18 to -14 dB
    - Forest / vegetation volume scattering: -12 to -8 dB
    - Urban double-bounce dihedral scattering: > -5 dB
    """
    arr = np.maximum(intensity.astype(np.float32), 1e-8)
    sigma0_db = 10.0 * np.log10(arr) + calibration_constant_db
    return np.clip(sigma0_db, -40.0, 15.0)
