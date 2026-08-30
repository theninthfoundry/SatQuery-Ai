"""Programmatic synthetic GeoTIFF generator for deterministic testing without large dataset downloads."""

from pathlib import Path
from typing import Tuple, Optional
import numpy as np

try:
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:  # pragma: no cover
    HAS_PIL = False


def create_synthetic_multiband_geotiff(
    output_path: Path | str,
    width: int = 64,
    height: int = 64,
    bands: int = 4,
    epsg: int = 32643,  # WGS 84 / UTM Zone 43N
    resolution: float = 10.0,  # 10m spatial resolution
    origin_x: float = 500000.0,
    origin_y: float = 3000000.0,
) -> Path:
    """Create a deterministic synthetic multi-band GeoTIFF with known CRS and coordinates."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not HAS_RASTERIO:
        raise RuntimeError("rasterio is required to create synthetic GeoTIFF fixture")

    transform = from_origin(origin_x, origin_y, resolution, resolution)
    crs = CRS.from_epsg(epsg)

    # Deterministic pixel data
    data = np.zeros((bands, height, width), dtype=np.uint16)
    for b in range(bands):
        # Create gradient patterns per band
        base_val = (b + 1) * 1000
        x_grad = np.linspace(0, 500, width, dtype=np.uint16)
        y_grad = np.linspace(0, 500, height, dtype=np.uint16)
        data[b] = base_val + x_grad[None, :] + y_grad[:, None]

    profile = {
        "driver": "GTiff",
        "dtype": "uint16",
        "nodata": 0,
        "width": width,
        "height": height,
        "count": bands,
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
    }

    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data)

    return out


def create_synthetic_singleband_geotiff(
    output_path: Path | str,
    width: int = 64,
    height: int = 64,
    epsg: int = 4326,  # WGS 84 Geographic
) -> Path:
    """Create a deterministic single-band GeoTIFF."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not HAS_RASTERIO:
        raise RuntimeError("rasterio is required to create synthetic GeoTIFF fixture")

    transform = from_origin(77.5946, 12.9716, 0.0001, 0.0001)
    crs = CRS.from_epsg(epsg)
    data = np.random.RandomState(42).uniform(10.0, 100.0, (1, height, width)).astype(np.float32)

    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": -9999.0,
        "width": width,
        "height": height,
        "count": 1,
        "crs": crs,
        "transform": transform,
    }

    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data)

    return out


def create_non_georeferenced_image(
    output_path: Path | str,
    width: int = 64,
    height: int = 64,
) -> Path:
    """Create a non-georeferenced standard RGB PNG image."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = 120  # Red
    arr[:, :, 1] = 200  # Green
    arr[:, :, 2] = 80   # Blue

    img = Image.fromarray(arr, mode="RGB")
    img.save(out, format="PNG")
    return out
