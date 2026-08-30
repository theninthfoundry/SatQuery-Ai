"""Geospatial core module for SatQuery AI."""

from .crs import inspect_crs, CRSInfo
from .raster import compute_band_stats, detect_modality, BandStatistics, ModalityDetection
from .metadata import extract_raster_metadata, RasterMetadata, BoundingBox, SpatialResolution
from .validation import validate_file_path, validate_raster_metadata, ValidationResult
from .geometry import pixel_to_coords, coords_to_pixel, bbox_to_geojson_polygon
from .tiling import generate_raster_tiles, RasterTileWindow

__all__ = [
    "inspect_crs",
    "CRSInfo",
    "compute_band_stats",
    "detect_modality",
    "BandStatistics",
    "ModalityDetection",
    "extract_raster_metadata",
    "RasterMetadata",
    "BoundingBox",
    "SpatialResolution",
    "validate_file_path",
    "validate_raster_metadata",
    "ValidationResult",
    "pixel_to_coords",
    "coords_to_pixel",
    "bbox_to_geojson_polygon",
    "generate_raster_tiles",
    "RasterTileWindow",
]
