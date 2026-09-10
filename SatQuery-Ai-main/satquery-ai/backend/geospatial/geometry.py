"""Geospatial geometry primitives, bounding box transforms, and coordinate math."""

from typing import Tuple, List, Dict, Any, Optional
import numpy as np

try:
    from shapely.geometry import box, Polygon, mapping
    import pyproj
    HAS_GEO = True
except ImportError:  # pragma: no cover
    HAS_GEO = False


def pixel_to_coords(
    x_pixel: float,
    y_pixel: float,
    transform: List[float],
) -> Tuple[float, float]:
    """Convert pixel (x, y) to spatial coordinates using 6-element affine transform [a, b, c, d, e, f]."""
    a, b, c, d, e, f = transform
    x_coord = a * x_pixel + b * y_pixel + c
    y_coord = d * x_pixel + e * y_pixel + f
    return x_coord, y_coord


def coords_to_pixel(
    x_coord: float,
    y_coord: float,
    transform: List[float],
) -> Tuple[float, float]:
    """Convert spatial coordinates to pixel coordinates by inverting affine transform."""
    a, b, c, d, e, f = transform
    det = a * e - b * d
    if det == 0:
        raise ValueError("Affine transform determinant is zero; singular matrix")
    x_pixel = (e * (x_coord - c) - b * (y_coord - f)) / det
    y_pixel = (-d * (x_coord - c) + a * (y_coord - f)) / det
    return x_pixel, y_pixel


def bbox_to_geojson_polygon(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
) -> Dict[str, Any]:
    """Create a GeoJSON polygon from bounding box coordinates."""
    if HAS_GEO:
        poly = box(min_x, min_y, max_x, max_y)
        return mapping(poly)
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_x, min_y],
                [max_x, min_y],
                [max_x, max_y],
                [min_x, max_y],
                [min_x, min_y],
            ]
        ],
    }
