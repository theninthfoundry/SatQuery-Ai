"""Test fixtures package."""

from .synthetic_raster import (
    create_synthetic_multiband_geotiff,
    create_synthetic_singleband_geotiff,
    create_non_georeferenced_image,
)

__all__ = [
    "create_synthetic_multiband_geotiff",
    "create_synthetic_singleband_geotiff",
    "create_non_georeferenced_image",
]
