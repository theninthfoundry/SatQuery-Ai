"""
Deterministic water-body detector (audit section 13, "the part I would
trust as the foundation of the product").

Pipeline (exactly the chain the audit specifies):
  band validation -> NDWI/MNDWI -> cloud/nodata masking -> adaptive
  threshold -> morphology -> connected components -> contours ->
  polygonization -> area -> candidate ranking

Two honesty rules enforced structurally, not just by convention:

1. CAPABILITY DEGRADATION: if the required bands for MNDWI/NDWI aren't
   present/labeled, this module returns capability=LIMITED and does NOT
   compute a spectral index. It never silently treats arbitrary 3-band
   imagery as if it were calibrated Sentinel-2 reflectance (audit
   section 13's "Critical correction").

2. AREA HONESTY: true geodesic area requires pyproj + shapely for CRS-
   aware reprojection. Those aren't installed in this sandbox (no network
   to pip install), so this module computes an explicitly-labeled
   PIXEL-GRID approximation (pixel_count * gsd^2) when pyproj/shapely are
   unavailable, and a real geodesic area when they are. The result object
   always tells you which one you got — it never claims "geodesic" when
   it only did a flat pixel-count multiply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

try:
    import cv2
    _HAS_CV2 = True
except ImportError:  # pragma: no cover
    _HAS_CV2 = False

try:
    from scipy import ndimage as _ndi
    _HAS_SCIPY = True
except ImportError:  # pragma: no cover
    _HAS_SCIPY = False

try:
    import shapely  # noqa: F401
    import pyproj  # noqa: F401
    _HAS_GEOSPATIAL_STACK = True
except ImportError:
    _HAS_GEOSPATIAL_STACK = False


class Capability(str, Enum):
    FULL = "FULL"          # MNDWI, calibrated bands present
    LIMITED = "LIMITED"     # bands unknown/insufficient; no spectral index computed
    UNAVAILABLE = "UNAVAILABLE"


class WaterDetectorError(ValueError):
    pass


@dataclass
class BandSet:
    """
    Caller must explicitly label which array is which band, sourced from
    real STAC asset metadata / ObservationRecord.assets keys — never
    inferred from array position.
    """
    green: Optional[np.ndarray] = None
    nir: Optional[np.ndarray] = None
    swir: Optional[np.ndarray] = None
    red: Optional[np.ndarray] = None
    nodata_mask: Optional[np.ndarray] = None   # True where nodata
    cloud_mask: Optional[np.ndarray] = None    # True where cloud


@dataclass
class WaterCandidate:
    candidate_id: int
    pixel_area: int
    area_m2: float
    area_ha: float
    area_method: str            # "geodesic" | "pixel_grid_approx"
    centroid_px: tuple[float, float]
    contour_px: list[tuple[int, int]]
    bbox_px: tuple[int, int, int, int]


@dataclass
class WaterDetectionResult:
    capability: Capability
    index_used: Optional[str]           # "MNDWI" | "NDWI" | None
    threshold: Optional[float]
    candidates: list[WaterCandidate] = field(default_factory=list)
    limitation_notes: list[str] = field(default_factory=list)

    @property
    def largest(self) -> Optional[WaterCandidate]:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.area_m2)


def _safe_index(numerator_band: np.ndarray, denom_band: np.ndarray) -> np.ndarray:
    num = numerator_band.astype(np.float64) - denom_band.astype(np.float64)
    den = numerator_band.astype(np.float64) + denom_band.astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        idx = np.where(den != 0, num / den, 0.0)
    return np.clip(idx, -1.0, 1.0)


def compute_water_index(bands: BandSet) -> tuple[Optional[np.ndarray], Optional[str], Capability, list[str]]:
    """
    Prefers MNDWI (Green, SWIR) over NDWI (Green, NIR) per audit section 13.
    Returns capability=LIMITED with no index if the required bands aren't present.
    """
    notes: list[str] = []

    if bands.green is not None and bands.swir is not None:
        if bands.green.shape != bands.swir.shape:
            raise WaterDetectorError("Green and SWIR bands have mismatched shapes.")
        return _safe_index(bands.green, bands.swir), "MNDWI", Capability.FULL, notes

    if bands.green is not None and bands.nir is not None:
        if bands.green.shape != bands.nir.shape:
            raise WaterDetectorError("Green and NIR bands have mismatched shapes.")
        notes.append("SWIR unavailable; used NDWI (Green/NIR) instead of preferred MNDWI.")
        return _safe_index(bands.green, bands.nir), "NDWI", Capability.FULL, notes

    notes.append(
        "Required spectral bands (Green+SWIR or Green+NIR) not present/labeled. "
        "Refusing to compute a water index on unknown-band imagery — "
        "capability degraded to LIMITED rather than faking NDWI on RGB data."
    )
    return None, None, Capability.LIMITED, notes


def _otsu_threshold(index: np.ndarray, valid_mask: np.ndarray) -> float:
    valid = index[valid_mask]
    if valid.size == 0:
        raise WaterDetectorError("No valid (non-masked) pixels to threshold.")
    scaled = ((valid + 1.0) * 127.5).astype(np.uint8)  # map [-1,1] -> [0,255]
    if _HAS_CV2:
        thresh_255, _ = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # Manual Otsu fallback so this still works without OpenCV.
        hist, _ = np.histogram(scaled, bins=256, range=(0, 256))
        total = scaled.size
        sum_all = np.dot(np.arange(256), hist)
        sum_b, w_b, max_var, thresh_255 = 0.0, 0.0, 0.0, 0
        for t in range(256):
            w_b += hist[t]
            if w_b == 0:
                continue
            w_f = total - w_b
            if w_f == 0:
                break
            sum_b += t * hist[t]
            m_b = sum_b / w_b
            m_f = (sum_all - sum_b) / w_f
            var_between = w_b * w_f * (m_b - m_f) ** 2
            if var_between > max_var:
                max_var = var_between
                thresh_255 = t
    return (thresh_255 / 127.5) - 1.0  # back to index space


def detect_water_bodies(
    bands: BandSet,
    *,
    gsd_m: float,
    pixel_to_geo=None,
    morphology_kernel_px: int = 3,
    min_pixel_area: int = 25,
) -> WaterDetectionResult:
    """
    Full deterministic pipeline. `pixel_to_geo` is an optional callable
    (px_row, px_col) -> (lon, lat) provided by the real rasterio affine
    transform; if given AND pyproj/shapely are installed, geodesic area
    is computed. Otherwise area is a labeled pixel-grid approximation.
    """
    index, index_name, capability, notes = compute_water_index(bands)
    if capability != Capability.FULL or index is None:
        return WaterDetectionResult(
            capability=capability, index_used=None, threshold=None,
            candidates=[], limitation_notes=notes,
        )

    valid_mask = np.ones(index.shape, dtype=bool)
    if bands.nodata_mask is not None:
        valid_mask &= ~bands.nodata_mask
    if bands.cloud_mask is not None:
        valid_mask &= ~bands.cloud_mask

    if valid_mask.sum() < min_pixel_area:
        notes.append("Insufficient valid (non-cloud/non-nodata) pixels for detection.")
        return WaterDetectionResult(
            capability=Capability.LIMITED, index_used=index_name, threshold=None,
            candidates=[], limitation_notes=notes,
        )

    threshold = _otsu_threshold(index, valid_mask)
    water_mask = (index > threshold) & valid_mask

    kernel = np.ones((morphology_kernel_px, morphology_kernel_px), np.uint8)
    if _HAS_CV2:
        mask_u8 = water_mask.astype(np.uint8)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
        water_mask = mask_u8.astype(bool)
    elif _HAS_SCIPY:
        water_mask = _ndi.binary_opening(water_mask, structure=kernel)
        water_mask = _ndi.binary_closing(water_mask, structure=kernel)

    if _HAS_SCIPY:
        labeled, n_components = _ndi.label(water_mask)
    elif _HAS_CV2:
        n_components, labeled = cv2.connectedComponents(water_mask.astype(np.uint8))
        n_components -= 1
    else:
        raise WaterDetectorError("Neither scipy nor cv2 available for connected components.")

    candidates: list[WaterCandidate] = []
    for comp_id in range(1, n_components + 1):
        comp_mask = (labeled == comp_id)
        pixel_area = int(comp_mask.sum())
        if pixel_area < min_pixel_area:
            continue

        ys, xs = np.nonzero(comp_mask)
        centroid_px = (float(xs.mean()), float(ys.mean()))
        bbox_px = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

        contour_px: list[tuple[int, int]] = []
        if _HAS_CV2:
            contours, _ = cv2.findContours(
                comp_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                contour_px = [(int(p[0][0]), int(p[0][1])) for p in largest_contour]

        area_m2, area_method = _compute_area(
            pixel_area=pixel_area, gsd_m=gsd_m,
            contour_px=contour_px, pixel_to_geo=pixel_to_geo,
        )

        candidates.append(WaterCandidate(
            candidate_id=comp_id,
            pixel_area=pixel_area,
            area_m2=area_m2,
            area_ha=area_m2 / 10_000.0,
            area_method=area_method,
            centroid_px=centroid_px,
            contour_px=contour_px,
            bbox_px=bbox_px,
        ))

    candidates.sort(key=lambda c: c.area_m2, reverse=True)

    return WaterDetectionResult(
        capability=Capability.FULL,
        index_used=index_name,
        threshold=float(threshold),
        candidates=candidates,
        limitation_notes=notes,
    )


def _compute_area(
    *, pixel_area: int, gsd_m: float, contour_px: list[tuple[int, int]], pixel_to_geo,
) -> tuple[float, str]:
    if pixel_to_geo is not None and _HAS_GEOSPATIAL_STACK and contour_px:
        from shapely.geometry import Polygon
        from pyproj import Geod
        lonlat_ring = [pixel_to_geo(row=py, col=px) for (px, py) in contour_px]
        if len(lonlat_ring) >= 3:
            poly = Polygon(lonlat_ring)
            geod = Geod(ellps="WGS84")
            area_m2 = abs(geod.geometry_area_perimeter(poly)[0])
            return area_m2, "geodesic"
    # Honest fallback — explicitly labeled, never presented as geodesic.
    return pixel_area * (gsd_m ** 2), "pixel_grid_approx"


def rank_candidates(result: WaterDetectionResult, *, operation: str = "largest") -> list[WaterCandidate]:
    if operation not in ("largest", "smallest"):
        raise ValueError("operation must be 'largest' or 'smallest'")
    return sorted(result.candidates, key=lambda c: c.area_m2, reverse=(operation == "largest"))
