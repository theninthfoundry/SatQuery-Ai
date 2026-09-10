"""Earth Observation Asset Descriptor — scientific data model for every uploaded satellite asset.

Every uploaded image becomes an EarthObservationAsset with full sensor metadata,
enabling the agent to reason about compatibility, modality, and processing requirements
before any model touches the data.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import rasterio
    import rasterio.warp
    import rasterio.windows
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


class Modality(str, Enum):
    """Sensor modality classification."""
    OPTICAL = "optical"
    SAR = "sar"
    MULTISPECTRAL = "multispectral"
    HYPERSPECTRAL = "hyperspectral"
    PANCHROMATIC = "panchromatic"
    UNKNOWN = "unknown"


class ProcessingLevel(str, Enum):
    """Standard remote sensing processing levels."""
    L0 = "L0"    # Raw instrument data
    L1A = "L1A"  # Reconstructed, unprocessed
    L1B = "L1B"  # Radiometrically corrected
    L1C = "L1C"  # Top-of-atmosphere reflectance (orthorectified)
    L2A = "L2A"  # Bottom-of-atmosphere reflectance (atmospherically corrected)
    L2B = "L2B"  # Surface reflectance + derived products
    GRD = "GRD"  # SAR Ground Range Detected
    SLC = "SLC"  # SAR Single Look Complex
    UNKNOWN = "unknown"


@dataclass
class BandInfo:
    """Metadata for a single raster band."""
    index: int
    dtype: str
    min_val: float
    max_val: float
    mean_val: float
    std_val: float
    nodata_val: Optional[float] = None
    wavelength_nm: Optional[float] = None  # Central wavelength in nanometers
    name: Optional[str] = None  # e.g., "B02", "VV", "Red"
    color_interp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "dtype": self.dtype,
            "min": self.min_val,
            "max": self.max_val,
            "mean": round(self.mean_val, 4),
            "std": round(self.std_val, 4),
            "nodata": self.nodata_val,
            "wavelength_nm": self.wavelength_nm,
            "name": self.name,
            "color_interp": self.color_interp,
        }


@dataclass
class BoundingBox:
    """Geographic bounding box in native and WGS84 CRS."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    wgs84: Optional[Dict[str, float]] = None  # {min_lon, min_lat, max_lon, max_lat}

    def area_degrees(self) -> float:
        """Approximate area in square degrees (for WGS84) or native units."""
        if self.wgs84:
            return abs(
                (self.wgs84["max_lon"] - self.wgs84["min_lon"])
                * (self.wgs84["max_lat"] - self.wgs84["min_lat"])
            )
        return abs((self.max_x - self.min_x) * (self.max_y - self.min_y))

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
        }
        if self.wgs84:
            d["wgs84"] = self.wgs84
        return d


@dataclass
class SpatialResolution:
    """Ground sampling distance (GSD) metadata."""
    x_res: float
    y_res: float
    units: str  # "metre", "degree", "pixel"

    @property
    def avg_gsd_m(self) -> float:
        """Average GSD in meters. Returns pixel-unit estimate if units are degrees."""
        if self.units == "degree":
            # Rough equatorial estimate: 1 degree ≈ 111320 m
            return (abs(self.x_res) + abs(self.y_res)) / 2.0 * 111320.0
        elif self.units == "pixel":
            return 1.0  # Unknown, assume 1m
        return (abs(self.x_res) + abs(self.y_res)) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_res": round(self.x_res, 6),
            "y_res": round(self.y_res, 6),
            "units": self.units,
            "avg_gsd_m": round(self.avg_gsd_m, 2),
        }


@dataclass
class EarthObservationAsset:
    """Complete scientific descriptor for a single Earth Observation asset.

    Every uploaded satellite image/raster becomes one of these. The agent
    reasons over assets — not raw file paths — to determine compatibility,
    select models, and validate analysis preconditions.
    """

    # Identity
    id: str
    path: Path
    filename: str
    checksum: str  # SHA256 of file content

    # Spatial properties
    width: int
    height: int
    crs: str
    epsg: Optional[int]
    bounds: Optional[BoundingBox]
    resolution: SpatialResolution
    transform: List[float]  # 6-element affine [a, b, c, d, e, f]
    georeferenced: bool

    # Spectral properties
    band_count: int
    bands: List[BandInfo]
    dtype: str

    # Sensor classification
    modality: Modality
    sensor: Optional[str] = None  # "Sentinel-2", "Cartosat-2S", "RISAT", etc.
    platform: Optional[str] = None  # "Sentinel-2A", "IRS-P5"

    # SAR-specific
    polarization: Optional[List[str]] = None  # ["VV", "VH"]
    orbit_direction: Optional[str] = None  # "ascending", "descending"
    incidence_angle: Optional[float] = None
    sigma0_calibrated: bool = False

    # Temporal
    acquisition_time: Optional[datetime] = None

    # Quality
    nodata_fraction: float = 0.0
    cloud_fraction: Optional[float] = None
    saturation_fraction: float = 0.0

    # Processing
    processing_level: ProcessingLevel = ProcessingLevel.UNKNOWN
    format: str = "unknown"
    driver: Optional[str] = None
    compression: Optional[str] = None

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "checksum": self.checksum,
            "width": self.width,
            "height": self.height,
            "crs": self.crs,
            "epsg": self.epsg,
            "bounds": self.bounds.to_dict() if self.bounds else None,
            "resolution": self.resolution.to_dict(),
            "transform": self.transform,
            "georeferenced": self.georeferenced,
            "band_count": self.band_count,
            "bands": [b.to_dict() for b in self.bands],
            "dtype": self.dtype,
            "modality": self.modality.value,
            "sensor": self.sensor,
            "platform": self.platform,
            "polarization": self.polarization,
            "orbit_direction": self.orbit_direction,
            "incidence_angle": self.incidence_angle,
            "sigma0_calibrated": self.sigma0_calibrated,
            "acquisition_time": self.acquisition_time.isoformat() if self.acquisition_time else None,
            "nodata_fraction": round(self.nodata_fraction, 4),
            "cloud_fraction": round(self.cloud_fraction, 4) if self.cloud_fraction is not None else None,
            "processing_level": self.processing_level.value,
            "format": self.format,
            "driver": self.driver,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @property
    def is_sar(self) -> bool:
        return self.modality == Modality.SAR

    @property
    def is_optical(self) -> bool:
        return self.modality in (Modality.OPTICAL, Modality.MULTISPECTRAL, Modality.PANCHROMATIC)

    @property
    def pixel_count(self) -> int:
        return self.width * self.height

    @property
    def has_valid_crs(self) -> bool:
        return self.georeferenced and self.crs not in ("", "None", "unknown")

    def summary(self) -> str:
        """Human-readable one-line summary."""
        mod = self.modality.value.upper()
        res = f"{self.resolution.avg_gsd_m:.1f}m"
        acq = self.acquisition_time.strftime("%Y-%m-%d") if self.acquisition_time else "unknown date"
        sensor = self.sensor or "unknown sensor"
        return f"{self.filename} | {sensor} {mod} | {self.width}×{self.height} | {res} GSD | {acq}"


# ──────────────────────────────────────────────────────────────────────────
# SENSOR WAVELENGTH REGISTRY
# ──────────────────────────────────────────────────────────────────────────

SENTINEL2_BANDS = {
    1: ("B01", 443.0),   # Coastal aerosol
    2: ("B02", 490.0),   # Blue
    3: ("B03", 560.0),   # Green
    4: ("B04", 665.0),   # Red
    5: ("B05", 705.0),   # Vegetation Red Edge
    6: ("B06", 740.0),   # Vegetation Red Edge
    7: ("B07", 783.0),   # Vegetation Red Edge
    8: ("B08", 842.0),   # NIR
    9: ("B8A", 865.0),   # NIR Narrow
    10: ("B09", 945.0),  # Water Vapour
    11: ("B10", 1375.0), # SWIR Cirrus
    12: ("B11", 1610.0), # SWIR
    13: ("B12", 2190.0), # SWIR
}

SENSOR_DETECTION_PATTERNS = {
    "sentinel-2": "Sentinel-2",
    "sentinel2": "Sentinel-2",
    "s2a": "Sentinel-2A",
    "s2b": "Sentinel-2B",
    "sentinel-1": "Sentinel-1",
    "sentinel1": "Sentinel-1",
    "s1a": "Sentinel-1A",
    "s1b": "Sentinel-1B",
    "cartosat": "Cartosat-2S",
    "resourcesat": "Resourcesat-2",
    "risat": "RISAT",
    "landsat": "Landsat",
    "worldview": "WorldView",
    "pleiades": "Pleiades",
}


class AssetFactory:
    """Factory for creating EarthObservationAsset instances from files."""

    @staticmethod
    def from_file(filepath: Path | str, asset_id: str) -> EarthObservationAsset:
        """Create a fully populated EarthObservationAsset from a raster file.

        Performs:
        1. SHA256 checksum computation
        2. Raster metadata extraction (CRS, bounds, transform, resolution)
        3. Per-band statistics (min, max, mean, std)
        4. Modality detection (optical/SAR/multispectral)
        5. Sensor identification from filename/tags
        6. Quality assessment (nodata fraction, potential cloud fraction)
        """
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Raster file not found: {p}")

        # 1. Compute checksum
        checksum = AssetFactory._compute_sha256(p)

        # 2. Extract metadata based on file type
        ext = p.suffix.lower()

        if HAS_RASTERIO and ext in (".tif", ".tiff", ".geotif", ".geotiff"):
            return AssetFactory._from_geotiff(p, asset_id, checksum)

        # Fallback to PIL for standard images
        return AssetFactory._from_standard_image(p, asset_id, checksum)

    @staticmethod
    def _from_geotiff(filepath: Path, asset_id: str, checksum: str) -> EarthObservationAsset:
        """Extract full metadata from a GeoTIFF using rasterio."""
        with rasterio.open(filepath) as ds:
            # CRS
            crs_str = str(ds.crs) if ds.crs else "None"
            epsg = ds.crs.to_epsg() if ds.crs else None

            # Transform
            t = ds.transform
            transform_list = [t.a, t.b, t.c, t.d, t.e, t.f]

            # Resolution
            x_res = abs(t.a) if t.a != 0 else 1.0
            y_res = abs(t.e) if t.e != 0 else 1.0
            crs_type = "projected" if ds.crs and ds.crs.is_projected else "geographic"
            units = "metre" if crs_type == "projected" else ("degree" if ds.crs else "pixel")
            resolution = SpatialResolution(
                x_res=round(x_res, 6), y_res=round(y_res, 6), units=units
            )

            # Bounds
            b = ds.bounds
            wgs84_bounds = None
            if ds.crs and ds.crs.is_valid:
                try:
                    if epsg == 4326:
                        wgs84_bounds = {
                            "min_lon": round(b.left, 6),
                            "min_lat": round(b.bottom, 6),
                            "max_lon": round(b.right, 6),
                            "max_lat": round(b.top, 6),
                        }
                    else:
                        wgs84_crs = CRS.from_epsg(4326)
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
                min_x=round(b.left, 4), min_y=round(b.bottom, 4),
                max_x=round(b.right, 4), max_y=round(b.top, 4),
                wgs84=wgs84_bounds,
            )

            # Band statistics
            bands: List[BandInfo] = []
            nodata_pixels = 0
            total_pixels = ds.width * ds.height

            for band_idx in range(1, ds.count + 1):
                data = ds.read(band_idx, window=rasterio.windows.Window(
                    0, 0, min(ds.width, 2048), min(ds.height, 2048)
                ))
                nodata_val = ds.nodatavals[band_idx - 1] if ds.nodatavals else None

                valid_mask = np.ones_like(data, dtype=bool)
                if nodata_val is not None:
                    valid_mask = data != nodata_val
                    nodata_pixels += int(np.sum(~valid_mask))

                valid_data = data[valid_mask].astype(np.float64)

                color_interp = None
                if ds.colorinterp and len(ds.colorinterp) >= band_idx:
                    color_interp = str(ds.colorinterp[band_idx - 1])

                bands.append(BandInfo(
                    index=band_idx,
                    dtype=str(ds.dtypes[band_idx - 1]) if ds.dtypes else "unknown",
                    min_val=float(np.min(valid_data)) if valid_data.size > 0 else 0.0,
                    max_val=float(np.max(valid_data)) if valid_data.size > 0 else 0.0,
                    mean_val=float(np.mean(valid_data)) if valid_data.size > 0 else 0.0,
                    std_val=float(np.std(valid_data)) if valid_data.size > 0 else 0.0,
                    nodata_val=nodata_val,
                    color_interp=color_interp,
                ))

            nodata_fraction = nodata_pixels / max(1, total_pixels * ds.count)

            # Modality detection
            tags = ds.tags() or {}
            modality = AssetFactory._detect_modality(
                band_count=ds.count,
                filename=filepath.name,
                tags=tags,
                bands=bands,
                color_interps=list(ds.colorinterp) if ds.colorinterp else None,
            )

            # Sensor detection
            sensor = AssetFactory._detect_sensor(filepath.name, tags)

            # SAR-specific metadata
            polarization = None
            sigma0_calibrated = False
            if modality == Modality.SAR:
                pol = tags.get("POLARIZATION", tags.get("polarization", ""))
                if pol:
                    polarization = [p.strip() for p in pol.split(",")]
                else:
                    # Guess from band count
                    if ds.count == 1:
                        polarization = ["VV"]
                    elif ds.count == 2:
                        polarization = ["VV", "VH"]

                # Check if values are in dB range (calibrated sigma0)
                if bands and bands[0].min_val < 0 and bands[0].max_val < 10:
                    sigma0_calibrated = True

            # Acquisition time
            acquisition_time = AssetFactory._parse_acquisition_time(tags, filepath.name)

            georeferenced = ds.crs is not None and ds.crs.is_valid

            return EarthObservationAsset(
                id=asset_id,
                path=filepath,
                filename=filepath.name,
                checksum=checksum,
                width=ds.width,
                height=ds.height,
                crs=crs_str,
                epsg=epsg,
                bounds=bounds,
                resolution=resolution,
                transform=transform_list,
                georeferenced=georeferenced,
                band_count=ds.count,
                bands=bands,
                dtype=str(ds.dtypes[0]) if ds.dtypes else "unknown",
                modality=modality,
                sensor=sensor,
                polarization=polarization,
                sigma0_calibrated=sigma0_calibrated,
                acquisition_time=acquisition_time,
                nodata_fraction=round(nodata_fraction, 4),
                processing_level=ProcessingLevel.UNKNOWN,
                format="GeoTIFF",
                driver=ds.driver,
                compression=ds.profile.get("compress"),
                tags=tags,
            )

    @staticmethod
    def _from_standard_image(filepath: Path, asset_id: str, checksum: str) -> EarthObservationAsset:
        """Fallback extraction for non-GeoTIFF images via PIL."""
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("PIL is required for non-GeoTIFF image processing")

        with Image.open(filepath) as img:
            width, height = img.size
            band_count = len(img.getbands())
            img_format = img.format or filepath.suffix.replace(".", "").upper()

            arr = np.array(img) if HAS_NUMPY else None
            bands: List[BandInfo] = []
            if arr is not None:
                if arr.ndim == 2:
                    bands.append(BandInfo(
                        index=1, dtype=str(arr.dtype),
                        min_val=float(np.min(arr)), max_val=float(np.max(arr)),
                        mean_val=float(np.mean(arr)), std_val=float(np.std(arr)),
                    ))
                elif arr.ndim == 3:
                    for b_idx in range(arr.shape[2]):
                        band_data = arr[:, :, b_idx]
                        bands.append(BandInfo(
                            index=b_idx + 1, dtype=str(arr.dtype),
                            min_val=float(np.min(band_data)), max_val=float(np.max(band_data)),
                            mean_val=float(np.mean(band_data)), std_val=float(np.std(band_data)),
                        ))

        return EarthObservationAsset(
            id=asset_id,
            path=filepath,
            filename=filepath.name,
            checksum=checksum,
            width=width,
            height=height,
            crs="None",
            epsg=None,
            bounds=None,
            resolution=SpatialResolution(x_res=1.0, y_res=1.0, units="pixel"),
            transform=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            georeferenced=False,
            band_count=band_count,
            bands=bands,
            dtype=str(arr.dtype) if arr is not None else "uint8",
            modality=Modality.OPTICAL if band_count <= 4 else Modality.MULTISPECTRAL,
            format=img_format,
            driver="PIL",
        )

    # ──────────────────────────────────────────────────────────────────────
    # CLASSIFICATION HELPERS
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _detect_modality(
        band_count: int,
        filename: str,
        tags: Dict[str, str],
        bands: List[BandInfo],
        color_interps: Optional[list] = None,
    ) -> Modality:
        """Classify sensor modality from available metadata signals."""
        fn_lower = filename.lower()
        tags_lower = {k.lower(): v.lower() for k, v in tags.items()}
        all_tags = " ".join(tags_lower.values())

        # Explicit SAR indicators
        sar_indicators = ["sar", "sentinel-1", "s1a", "s1b", "risat", "radarsat",
                          "alos2", "palsar", "sigma0", "backscatter", "vv", "vh",
                          "hh", "hv", "grd", "slc"]
        if any(ind in fn_lower or ind in all_tags for ind in sar_indicators):
            return Modality.SAR

        # SAR-like value ranges (dB scale, negative values)
        if bands and band_count <= 2:
            if bands[0].min_val < -30 and bands[0].max_val < 10:
                return Modality.SAR

        # Hyperspectral
        if band_count > 20:
            return Modality.HYPERSPECTRAL

        # Multispectral
        if band_count > 4:
            return Modality.MULTISPECTRAL

        # Panchromatic
        if band_count == 1:
            if color_interps and str(color_interps[0]) == "ColorInterp.gray":
                return Modality.PANCHROMATIC
            return Modality.OPTICAL

        return Modality.OPTICAL

    @staticmethod
    def _detect_sensor(filename: str, tags: Dict[str, str]) -> Optional[str]:
        """Identify sensor platform from filename and metadata tags."""
        search_text = filename.lower() + " " + " ".join(
            v.lower() for v in tags.values()
        )
        for pattern, sensor_name in SENSOR_DETECTION_PATTERNS.items():
            if pattern in search_text:
                return sensor_name
        return None

    @staticmethod
    def _parse_acquisition_time(tags: Dict[str, str], filename: str) -> Optional[datetime]:
        """Attempt to extract acquisition timestamp from metadata or filename."""
        # Check common metadata keys
        for key in ["TIFFTAG_DATETIME", "datetime", "acquisition_date",
                     "DATE_ACQUIRED", "SENSING_TIME", "ACQUISITIONDATE"]:
            val = tags.get(key)
            if val:
                for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        return datetime.strptime(val.strip(), fmt)
                    except ValueError:
                        continue

        # Try parsing date from filename (common patterns: 20240315, 2024-03-15)
        import re
        patterns = [
            r"(\d{4})(\d{2})(\d{2})",  # 20240315
            r"(\d{4})-(\d{2})-(\d{2})",  # 2024-03-15
        ]
        for pat in patterns:
            match = re.search(pat, filename)
            if match:
                try:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if 1990 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                        return datetime(year, month, day)
                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def _compute_sha256(filepath: Path, chunk_size: int = 65536) -> str:
        """Compute SHA256 hash of file content."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
