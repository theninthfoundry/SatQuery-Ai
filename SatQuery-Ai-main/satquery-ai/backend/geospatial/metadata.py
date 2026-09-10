"""Comprehensive raster metadata extraction engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .crs import inspect_crs, CRSInfo
from .raster import compute_band_stats, detect_modality, BandStatistics, ModalityDetection

try:
    import rasterio
    import rasterio.warp
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:  # pragma: no cover
    HAS_PIL = False


@dataclass
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    wgs84: Optional[Dict[str, float]] = None  # {min_lon, min_lat, max_lon, max_lat}


@dataclass
class SpatialResolution:
    x_res: float
    y_res: float
    units: str  # "metre", "degree", "pixel", etc.


@dataclass
class RasterMetadata:
    filename: str
    format: str
    driver: Optional[str]
    width: int
    height: int
    band_count: int
    dtype: str
    crs: CRSInfo
    transform: List[float]
    bounds: Optional[BoundingBox]
    resolution: SpatialResolution
    nodata: Optional[float]
    compression: Optional[str]
    bands: List[BandStatistics] = field(default_factory=list)
    modality: ModalityDetection = field(default_factory=lambda: ModalityDetection("unknown", 0.0, []))
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "format": self.format,
            "driver": self.driver,
            "width": self.width,
            "height": self.height,
            "band_count": self.band_count,
            "dtype": self.dtype,
            "crs": self.crs.to_dict(),
            "transform": self.transform,
            "bounds": {
                "min_x": self.bounds.min_x,
                "min_y": self.bounds.min_y,
                "max_x": self.bounds.max_x,
                "max_y": self.bounds.max_y,
                "wgs84": self.bounds.wgs84,
            } if self.bounds else None,
            "resolution": {
                "x_res": self.resolution.x_res,
                "y_res": self.resolution.y_res,
                "units": self.resolution.units,
            },
            "nodata": self.nodata,
            "compression": self.compression,
            "bands": [
                {
                    "band_index": b.band_index,
                    "dtype": b.dtype,
                    "min": b.min,
                    "max": b.max,
                    "mean": b.mean,
                    "std": b.std,
                    "nodata": b.nodata,
                }
                for b in self.bands
            ],
            "modality": {
                "detected": self.modality.modality,
                "confidence": self.modality.confidence,
                "basis": self.modality.basis,
            },
            "tags": self.tags,
        }


def extract_raster_metadata(filepath: Path | str) -> RasterMetadata:
    """Extract full metadata, CRS, bounding box, resolution, and band statistics from a raster or image."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"Raster file not found: {p}")

    ext = p.suffix.lower()

    if HAS_RASTERIO and ext in [".tif", ".tiff", ".geotif", ".geotiff"]:
        with rasterio.open(p) as ds:
            # 1. CRS
            crs_info = inspect_crs(ds.crs)

            # 2. Transform & Resolution
            t = ds.transform
            transform_list = [t.a, t.b, t.c, t.d, t.e, t.f]
            x_res = abs(t.a) if t.a != 0 else 1.0
            y_res = abs(t.e) if t.e != 0 else 1.0
            units = crs_info.units or ("metre" if crs_info.crs_type == "projected" else "pixel")
            resolution = SpatialResolution(x_res=round(x_res, 6), y_res=round(y_res, 6), units=units)

            # 3. Bounds & WGS84 Reprojection
            b = ds.bounds
            wgs84_bounds = None
            if ds.crs and ds.crs.is_valid:
                try:
                    wgs84_crs = CRS.from_epsg(4326)
                    if ds.crs.to_epsg() == 4326:
                        wgs84_bounds = {
                            "min_lon": round(b.left, 6),
                            "min_lat": round(b.bottom, 6),
                            "max_lon": round(b.right, 6),
                            "max_lat": round(b.top, 6),
                        }
                    else:
                        xs = [b.left, b.right, b.left, b.right]
                        ys = [b.bottom, b.bottom, b.top, b.top]
                        lons, lats = rasterio.warp.transform(ds.crs, wgs84_crs, xs, ys)
                        wgs84_bounds = {
                            "min_lon": round(min(lons), 6),
                            "min_lat": round(min(lats), 6),
                            "max_lon": round(max(lons), 6),
                            "max_lat": round(max(lats), 6),
                        }
                except Exception:
                    pass

            bounds = BoundingBox(
                min_x=round(b.left, 4),
                min_y=round(b.bottom, 4),
                max_x=round(b.right, 4),
                max_y=round(b.top, 4),
                wgs84=wgs84_bounds,
            )

            # 4. Band Stats
            bands_stats: List[BandStatistics] = []
            for b_idx in range(1, ds.count + 1):
                nodata_val = ds.nodatavals[b_idx - 1] if ds.nodatavals else None
                stats = compute_band_stats(ds, band_idx=b_idx, nodata_val=nodata_val)
                bands_stats.append(stats)

            # 5. Modality
            profile = ds.profile
            tags = ds.tags() or {}
            color_interps = list(ds.colorinterp) if ds.colorinterp else None
            modality = detect_modality(
                band_count=ds.count,
                filename=p.name,
                color_interps=color_interps,
                tags=tags,
                band_stats=bands_stats,
            )

            return RasterMetadata(
                filename=p.name,
                format="GeoTIFF",
                driver=ds.driver,
                width=ds.width,
                height=ds.height,
                band_count=ds.count,
                dtype=ds.dtypes[0] if ds.dtypes else "unknown",
                crs=crs_info,
                transform=transform_list,
                bounds=bounds,
                resolution=resolution,
                nodata=ds.nodata,
                compression=profile.get("compress"),
                bands=bands_stats,
                modality=modality,
                tags=tags,
            )

    # Fallback to standard image handling via PIL
    if HAS_PIL:
        with Image.open(p) as img:
            width, height = img.size
            bands_str = img.getbands()
            band_count = len(bands_str)
            img_format = img.format or ext.replace(".", "").upper()

            # Inspect bands stats
            np_img = np.array(img)
            bands_stats = []
            if np_img.ndim == 2:
                bands_stats.append(compute_band_stats(np_img, band_idx=1))
            elif np_img.ndim == 3:
                for b_idx in range(np_img.shape[2]):
                    bands_stats.append(compute_band_stats(np_img[:, :, b_idx], band_idx=b_idx + 1))

            crs_info = inspect_crs(None)  # Missing CRS
            modality = detect_modality(band_count=band_count, filename=p.name)

            return RasterMetadata(
                filename=p.name,
                format=img_format,
                driver="PIL",
                width=width,
                height=height,
                band_count=band_count,
                dtype=str(np_img.dtype),
                crs=crs_info,
                transform=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                bounds=None,
                resolution=SpatialResolution(x_res=1.0, y_res=1.0, units="pixel"),
                nodata=None,
                compression=None,
                bands=bands_stats,
                modality=modality,
                tags={},
            )

    raise RuntimeError("No suitable image reader (rasterio or PIL) available")
