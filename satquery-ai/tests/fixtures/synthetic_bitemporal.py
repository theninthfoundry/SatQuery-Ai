"""Programmatic synthetic bi-temporal GeoTIFF pair generator for testing change detection."""

from pathlib import Path
from typing import Tuple
import numpy as np

try:
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False


def create_synthetic_bitemporal_pair(
    dir_path: Path | str,
    width: int = 64,
    height: int = 64,
    epsg: int = 32643,
    resolution: float = 10.0,
    change_box_size: int = 16,
) -> Tuple[Path, Path]:
    """Create a deterministic before and after GeoTIFF pair with a known changed square in the center.
    
    The changed square has dimensions (change_box_size x change_box_size) pixels.
    At 10m resolution, a 16x16 square = 160m x 160m = 25,600 m².
    Total area = 64x64 = 4,096 pixels = 409,600 m².
    Change % = (256 / 4096) * 100 = 6.25%.
    """
    out_dir = Path(dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not HAS_RASTERIO:
        raise RuntimeError("rasterio is required to create synthetic bi-temporal pair")

    before_path = out_dir / "before.tif"
    after_path = out_dir / "after.tif"

    transform = from_origin(500000.0, 3000000.0, resolution, resolution)
    crs = CRS.from_epsg(epsg)

    # Base image: 3-band uniform optical scene
    before_data = np.full((3, height, width), 100, dtype=np.uint8)

    # After image: same scene with a bright changed square in the center
    after_data = np.copy(before_data)
    y_start = (height - change_box_size) // 2
    x_start = (width - change_box_size) // 2
    after_data[:, y_start : y_start + change_box_size, x_start : x_start + change_box_size] = 240

    profile = {
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": None,
        "width": width,
        "height": height,
        "count": 3,
        "crs": crs,
        "transform": transform,
    }

    with rasterio.open(before_path, "w", **profile) as dst:
        dst.write(before_data)

    with rasterio.open(after_path, "w", **profile) as dst:
        dst.write(after_data)

    return before_path, after_path
