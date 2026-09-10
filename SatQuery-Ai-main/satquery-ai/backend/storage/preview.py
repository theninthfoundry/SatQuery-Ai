"""Web-compatible raster preview generator with dynamic percentile contrast stretching."""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np

try:
    import rasterio
    from rasterio.enums import Resampling
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:  # pragma: no cover
    HAS_PIL = False


def normalize_band_to_uint8(
    band_data: np.ndarray,
    p_low: float = 2.0,
    p_high: float = 98.0,
    nodata_val: Optional[float] = None,
) -> np.ndarray:
    """Normalize arbitrary raster band (12-bit, 16-bit, float) to 8-bit uint8 (0-255) using percentile stretch."""
    arr = np.asarray(band_data, dtype=np.float64)
    valid_mask = np.isfinite(arr)
    if nodata_val is not None:
        valid_mask &= (arr != nodata_val)

    valid_vals = arr[valid_mask]
    if valid_vals.size == 0:
        return np.zeros(arr.shape, dtype=np.uint8)

    vmin = np.percentile(valid_vals, p_low)
    vmax = np.percentile(valid_vals, p_high)

    if vmax <= vmin:
        vmax = vmin + 1.0

    # Stretch & clip
    norm = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0)
    uint8_data = (norm * 255.0).astype(np.uint8)
    return uint8_data


def generate_raster_preview(
    raster_path: Path | str,
    output_png_path: Path | str,
    max_dimension: int = 1024,
) -> Path:
    """Generate a clean, web-compatible PNG preview from a GeoTIFF or image file."""
    r_path = Path(raster_path)
    out_path = Path(output_png_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ext = r_path.suffix.lower()

    if HAS_RASTERIO and ext in [".tif", ".tiff", ".geotif", ".geotiff"]:
        with rasterio.open(r_path) as ds:
            width, height = ds.width, ds.height
            scale = min(1.0, max_dimension / max(width, height))
            out_width = max(1, int(width * scale))
            out_height = max(1, int(height * scale))

            band_count = ds.count
            nodata_val = ds.nodata

            if band_count == 1:
                # Single band (e.g. SAR or Grayscale)
                band_arr = ds.read(
                    1,
                    out_shape=(out_height, out_width),
                    resampling=Resampling.bilinear,
                )
                img_8bit = normalize_band_to_uint8(band_arr, nodata_val=nodata_val)
                img = Image.fromarray(img_8bit, mode="L")
            elif band_count == 3:
                # 3-Band RGB
                r = ds.read(1, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                g = ds.read(2, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                b = ds.read(3, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                r_8 = normalize_band_to_uint8(r, nodata_val=nodata_val)
                g_8 = normalize_band_to_uint8(g, nodata_val=nodata_val)
                b_8 = normalize_band_to_uint8(b, nodata_val=nodata_val)
                rgb_arr = np.stack([r_8, g_8, b_8], axis=-1)
                img = Image.fromarray(rgb_arr, mode="RGB")
            else:
                # Multi-band (>3): default to bands 1, 2, 3
                r = ds.read(1, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                g = ds.read(2, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                b = ds.read(3, out_shape=(out_height, out_width), resampling=Resampling.bilinear)
                r_8 = normalize_band_to_uint8(r, nodata_val=nodata_val)
                g_8 = normalize_band_to_uint8(g, nodata_val=nodata_val)
                b_8 = normalize_band_to_uint8(b, nodata_val=nodata_val)
                rgb_arr = np.stack([r_8, g_8, b_8], axis=-1)
                img = Image.fromarray(rgb_arr, mode="RGB")

            img.save(out_path, format="PNG", optimize=True)
            return out_path

    # Fallback to standard PIL
    if HAS_PIL:
        with Image.open(r_path) as img:
            img = img.convert("RGBA" if img.mode == "RGBA" else "RGB")
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            img.save(out_path, format="PNG", optimize=True)
            return out_path

    raise RuntimeError("No image processing backend available for preview generation")
