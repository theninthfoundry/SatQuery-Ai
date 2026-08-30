"""Programmatic synthetic Optical + SAR co-registered GeoTIFF pair generator."""

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


def create_synthetic_optical_sar_pair(
    dir_path: Path | str,
    width: int = 64,
    height: int = 64,
    epsg: int = 32643,
    resolution: float = 10.0,
) -> Tuple[Path, Path]:
    """Create a co-registered Optical RGB GeoTIFF (3-band) and SAR Backscatter GeoTIFF (1-band float32)."""
    out_dir = Path(dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not HAS_RASTERIO:
        raise RuntimeError("rasterio is required to create synthetic optical-sar pair")

    optical_path = out_dir / "sentinel2_optical.tif"
    sar_path = out_dir / "sentinel1_sar.tif"

    transform = from_origin(500000.0, 3000000.0, resolution, resolution)
    crs = CRS.from_epsg(epsg)

    # 1. Optical Data: 3-band RGB (Values 50 - 220)
    opt_data = np.zeros((3, height, width), dtype=np.uint8)
    opt_data[0] = np.random.RandomState(42).randint(80, 200, (height, width), dtype=np.uint8)  # Red
    opt_data[1] = np.random.RandomState(43).randint(90, 220, (height, width), dtype=np.uint8)  # Green
    opt_data[2] = np.random.RandomState(44).randint(60, 180, (height, width), dtype=np.uint8)  # Blue

    # Add a water body in top-left (low red/green, moderate blue)
    opt_data[0, :20, :20] = 30
    opt_data[1, :20, :20] = 50
    opt_data[2, :20, :20] = 160

    with rasterio.open(
        optical_path,
        "w",
        driver="GTiff",
        dtype="uint8",
        width=width,
        height=height,
        count=3,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(opt_data)
        dst.set_tag_item("SENSOR_TYPE", "OPTICAL_SENTINEL2")

    # 2. SAR Data: 1-band Radar Backscatter Sigma0 in dB (-25.0 to 0.0 dB)
    sar_data = np.random.RandomState(45).uniform(-18.0, -8.0, (1, height, width)).astype(np.float32)
    # Water has specular reflection -> very low backscatter (-24 dB)
    sar_data[0, :20, :20] = -23.5

    with rasterio.open(
        sar_path,
        "w",
        driver="GTiff",
        dtype="float32",
        width=width,
        height=height,
        count=1,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(sar_data)
        dst.set_tag_item("SENSOR_TYPE", "SAR_SENTINEL1_GRD")
        dst.set_tag_item("POLARIZATION", "VV")

    return optical_path, sar_path
