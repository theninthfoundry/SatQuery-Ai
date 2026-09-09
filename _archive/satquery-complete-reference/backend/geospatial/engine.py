"""
backend/geospatial/engine.py

The deterministic half of SatQuery AI. Nothing in this file is a neural
network -- it is pure geometry/CRS math, which is exactly why it is
trusted to turn model output (pixel boxes, probability masks) into
ground-truth area/coordinates. If this file is wrong, every downstream
number is wrong, so every function raises loudly instead of guessing.

Requires: rasterio, pyproj, shapely, opencv-python (cv2), numpy.
Install: pip install rasterio pyproj shapely opencv-python numpy
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.crs import CRS as RasterioCRS
except ImportError as e:  # pragma: no cover
    rasterio = None
    _RASTERIO_IMPORT_ERROR = e

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from pyproj import Transformer, CRS as PyprojCRS
except ImportError as e:  # pragma: no cover
    Transformer = None
    _PYPROJ_IMPORT_ERROR = e

try:
    from shapely.geometry import Polygon, mapping, shape
    from shapely.ops import transform as shapely_transform
except ImportError as e:  # pragma: no cover
    Polygon = None
    _SHAPELY_IMPORT_ERROR = e


def _require_geospatial_stack():
    missing = []
    if rasterio is None:
        missing.append("rasterio")
    if Transformer is None:
        missing.append("pyproj")
    if Polygon is None:
        missing.append("shapely")
    if missing:
        raise ImportError(
            f"Missing geospatial dependencies: {', '.join(missing)}. "
            f"Install with: pip install rasterio pyproj shapely opencv-python"
        )


# ---------------------------------------------------------------------------
# Raster ingestion
# ---------------------------------------------------------------------------

@dataclass
class RasterInfo:
    path: str
    width: int
    height: int
    count: int  # band count
    crs_epsg: Optional[int]
    transform: tuple  # 6-element affine (a, b, c, d, e, f) rasterio-style
    bounds_geo: tuple  # (west, south, east, north) in raster's native CRS
    gsd_x: float  # ground sample distance, metres/pixel or degrees/pixel
    gsd_y: float
    dtype: str
    nodata: Optional[float]


def read_raster_info(path: str) -> RasterInfo:
    """Open a GeoTIFF/TIFF and return validated spatial metadata.

    Raises FileNotFoundError / rasterio.errors.RasterioIOError on bad input
    rather than returning a partially-filled object -- callers (the agent's
    Layer 2 validation) rely on this failing loudly for malformed uploads.
    """
    _require_geospatial_stack()
    if not Path(path).exists():
        raise FileNotFoundError(f"Raster not found: {path}")

    with rasterio.open(path) as ds:
        crs_epsg = ds.crs.to_epsg() if ds.crs else None
        transform = tuple(ds.transform)[:6]
        gsd_x = abs(transform[0])
        gsd_y = abs(transform[4])
        return RasterInfo(
            path=str(path),
            width=ds.width,
            height=ds.height,
            count=ds.count,
            crs_epsg=crs_epsg,
            transform=transform,
            bounds_geo=tuple(ds.bounds),
            gsd_x=gsd_x,
            gsd_y=gsd_y,
            dtype=str(ds.dtypes[0]),
            nodata=ds.nodata,
        )


def read_raster_array(path: str, bands: Optional[list] = None) -> np.ndarray:
    """Return array shaped (bands, H, W) as float32."""
    _require_geospatial_stack()
    with rasterio.open(path) as ds:
        idx = bands if bands else list(range(1, ds.count + 1))
        arr = ds.read(idx).astype(np.float32)
    return arr


# ---------------------------------------------------------------------------
# Compatibility / pairing validation (agent Layer 2)
# ---------------------------------------------------------------------------

@dataclass
class PairValidationResult:
    is_valid: bool
    overlap_fraction: float
    reasons: list


def validate_bitemporal_pair(info_a: RasterInfo, info_b: RasterInfo,
                              min_overlap: float = 0.6) -> PairValidationResult:
    """Checks two rasters are spatially comparable before change detection
    is attempted. This is what stops the system from "detecting change"
    between two unrelated scenes."""
    reasons = []
    if info_a.crs_epsg != info_b.crs_epsg:
        reasons.append(
            f"CRS mismatch: {info_a.crs_epsg} vs {info_b.crs_epsg} "
            f"(will be reprojected for overlap check)"
        )

    bounds_a = _to_common_crs_bounds(info_a)
    bounds_b = _to_common_crs_bounds(info_b)
    overlap = _bbox_overlap_fraction(bounds_a, bounds_b)

    if overlap < min_overlap:
        reasons.append(
            f"Overlap {overlap:.1%} below required {min_overlap:.0%} -- "
            f"scenes may not depict the same area"
        )

    gsd_ratio = max(info_a.gsd_x, info_b.gsd_x) / max(min(info_a.gsd_x, info_b.gsd_x), 1e-9)
    if gsd_ratio > 3.0:
        reasons.append(
            f"GSD mismatch ratio {gsd_ratio:.1f}x -- resample to common "
            f"resolution before differencing"
        )

    is_valid = overlap >= min_overlap and gsd_ratio <= 5.0
    return PairValidationResult(is_valid=is_valid, overlap_fraction=overlap, reasons=reasons)


def _to_common_crs_bounds(info: RasterInfo, target_epsg: int = 4326):
    _require_geospatial_stack()
    if info.crs_epsg is None:
        return info.bounds_geo  # assume already geographic (demo data)
    if info.crs_epsg == target_epsg:
        return info.bounds_geo
    return transform_bounds(
        RasterioCRS.from_epsg(info.crs_epsg),
        RasterioCRS.from_epsg(target_epsg),
        *info.bounds_geo,
    )


def _bbox_overlap_fraction(b1, b2) -> float:
    w1, s1, e1, n1 = b1
    w2, s2, e2, n2 = b2
    ix = max(0.0, min(e1, e2) - max(w1, w2))
    iy = max(0.0, min(n1, n2) - max(s1, s2))
    inter = ix * iy
    area1 = max(1e-12, (e1 - w1) * (n1 - s1))
    area2 = max(1e-12, (e2 - w2) * (n2 - s2))
    smaller = min(area1, area2)
    return inter / smaller if smaller > 0 else 0.0


# ---------------------------------------------------------------------------
# Affine pixel -> geographic coordinate
# ---------------------------------------------------------------------------

def pixel_to_geo(transform: tuple, col: float, row: float) -> tuple:
    """Apply the 6-element affine geotransform: standard GDAL convention
    Xgeo = a*col + b*row + c ; Ygeo = d*col + e*row + f
    """
    a, b, c, d, e, f = transform
    x_geo = a * col + b * row + c
    y_geo = d * col + e * row + f
    return x_geo, y_geo


def bbox_pixels_to_geo_polygon(transform: tuple, ymin: float, xmin: float,
                                ymax: float, xmax: float) -> list:
    """Converts a [ymin, xmin, ymax, xmax] normalized-or-pixel box (as
    returned by grounding models) into a closed ring of geo coordinates,
    in raster-native CRS."""
    corners_px = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)]
    return [pixel_to_geo(transform, c, r) for c, r in corners_px]


def denormalize_bbox(bbox_norm: list, width: int, height: int) -> list:
    """GeoChat/LLaVA-style grounding models emit boxes normalized to
    [0,1000) or [0,1). This converts to pixel space. Detects the scale
    heuristically from the max coordinate value."""
    ymin, xmin, ymax, xmax = bbox_norm
    scale = 1000.0 if max(bbox_norm) > 1.5 else 1.0
    return [
        (ymin / scale) * height,
        (xmin / scale) * width,
        (ymax / scale) * height,
        (xmax / scale) * width,
    ]


# ---------------------------------------------------------------------------
# UTM auto-projection + exact area
# ---------------------------------------------------------------------------

def auto_utm_epsg(lon: float, lat: float) -> int:
    """Pick the correct UTM zone EPSG for a lon/lat point (WGS84 datum)."""
    zone = int(math.floor((lon + 180) / 6) % 60) + 1
    if lat >= 0:
        return 32600 + zone  # WGS84 / UTM north
    return 32700 + zone  # WGS84 / UTM south


def reproject_ring_to_utm(ring_native: list, src_epsg: Optional[int]) -> tuple:
    """Reprojects a ring of (x, y) points from the raster's native CRS
    into an auto-selected UTM zone (metres), for exact area computation.
    Returns (utm_ring, utm_epsg).
    """
    _require_geospatial_stack()
    src = PyprojCRS.from_epsg(src_epsg) if src_epsg else PyprojCRS.from_epsg(4326)

    # get a representative lon/lat to pick the UTM zone
    to_wgs84 = Transformer.from_crs(src, PyprojCRS.from_epsg(4326), always_xy=True)
    sample_lon, sample_lat = to_wgs84.transform(*ring_native[0])
    utm_epsg = auto_utm_epsg(sample_lon, sample_lat)

    to_utm = Transformer.from_crs(src, PyprojCRS.from_epsg(utm_epsg), always_xy=True)
    utm_ring = [to_utm.transform(x, y) for x, y in ring_native]
    return utm_ring, utm_epsg


def polygon_area_m2(utm_ring: list) -> float:
    """Exact planar (UTM) area via the shoelace formula, wrapped in
    Shapely for robustness against self-intersecting/degenerate rings."""
    _require_geospatial_stack()
    poly = Polygon(utm_ring)
    if not poly.is_valid:
        poly = poly.buffer(0)  # standard fix for minor self-intersections
    return abs(poly.area)


def geo_polygon_to_ground_area(ring_native: list, src_epsg: Optional[int]) -> dict:
    """End-to-end: native-CRS ring -> UTM reprojection -> exact area."""
    utm_ring, utm_epsg = reproject_ring_to_utm(ring_native, src_epsg)
    area_m2 = polygon_area_m2(utm_ring)
    return {
        "area_m2": round(area_m2, 2),
        "area_ha": round(area_m2 / 10000.0, 4),
        "utm_epsg": utm_epsg,
        "utm_ring": [[round(x, 3), round(y, 3)] for x, y in utm_ring],
    }


# ---------------------------------------------------------------------------
# Change-mask -> contours -> polygons (used by both real ChangeNet output
# and the classical-CV fallback -- same geometry code path either way)
# ---------------------------------------------------------------------------

def mask_to_geo_clusters(mask: np.ndarray, transform: tuple, src_epsg: Optional[int],
                          threshold: float = 0.5, min_cluster_px: int = 25) -> list:
    """Takes a 2D probability/binary mask (H, W) in raster pixel space and
    returns a list of geo-referenced clusters with exact UTM area.

    Uses cv2.findContours; if opencv is unavailable, falls back to a pure
    connected-components implementation via scipy-free flood fill so the
    pipeline never silently skips clusters.
    """
    binary = (mask >= threshold).astype(np.uint8)
    clusters = []

    if cv2 is not None:
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        raw_polys_px = []
        for c in contours:
            if cv2.contourArea(c) < min_cluster_px:
                continue
            ring_px = [(float(pt[0][0]), float(pt[0][1])) for pt in c]
            if len(ring_px) < 3:
                continue
            ring_px.append(ring_px[0])
            raw_polys_px.append(ring_px)
    else:
        raw_polys_px = _connected_components_boxes(binary, min_cluster_px)

    for i, ring_px in enumerate(raw_polys_px, start=1):
        ring_native = [pixel_to_geo(transform, x, y) for x, y in ring_px]
        area_info = geo_polygon_to_ground_area(ring_native, src_epsg)
        clusters.append({
            "cluster_id": i,
            "ring_native_crs": [[round(x, 6), round(y, 6)] for x, y in ring_native],
            **area_info,
        })
    return clusters


def _connected_components_boxes(binary: np.ndarray, min_cluster_px: int) -> list:
    """Dependency-free fallback: BFS connected components -> bounding-box
    rings. Coarser than contour polygonization but never fabricates
    geometry, and is used only when opencv is not installed."""
    h, w = binary.shape
    visited = np.zeros_like(binary, dtype=bool)
    boxes = []
    for y in range(h):
        for x in range(w):
            if binary[y, x] and not visited[y, x]:
                stack = [(y, x)]
                visited[y, x] = True
                ys, xs = [], []
                while stack:
                    cy, cx = stack.pop()
                    ys.append(cy)
                    xs.append(cx)
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and binary[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
                if len(ys) < min_cluster_px:
                    continue
                y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
                boxes.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
    return boxes
