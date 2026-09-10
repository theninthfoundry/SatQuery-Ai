"""Deterministic Water Body Analyzer for remote sensing imagery.

Performs scientifically grounded water detection, morphology, connected component
analysis, contour polygonization, and WGS84 geodesic area measurement.

Pipeline:
1. Raster Ingestion & Band Identification (Green, NIR, SWIR).
2. Nodata and cloud/shadow masking.
3. NDWI / MNDWI spectral water index calculation.
4. Adaptive / Otsu or calibrated thresholding.
5. Morphological opening & closing (speckle removal, hole filling).
6. Connected components labeling.
7. Vector polygonization of actual contour boundaries (no bounding rectangles!).
8. WGS84 geodesic area (m², ha), perimeter, and centroid calculation.
9. Candidate ranking (argmax area).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from .cloud import CloudQualityEstimator, CloudQualityResult

try:
    import rasterio
    import rasterio.features
    from rasterio.warp import transform_geom
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    from shapely.geometry import shape, Polygon, MultiPolygon, mapping
    from shapely.ops import unary_union
    import pyproj
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

try:
    import scipy.ndimage as ndi
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


@dataclass
class WaterBodyCandidate:
    """A detected, measured, and polygonized contiguous water body."""
    id: str
    pixel_count: int
    area_m2: float
    area_ha: float
    perimeter_m: float
    centroid: Dict[str, float]  # {"lat": ..., "lon": ...}
    bbox: Dict[str, float]  # {"ymin": ..., "xmin": ..., "ymax": ..., "xmax": ...}
    geometry: Dict[str, Any]  # GeoJSON Polygon / MultiPolygon
    index_method: str  # "MNDWI" or "NDWI"
    threshold: float
    valid_pixel_fraction: float
    spectral_mean: float = 0.0
    area_uncertainty_m2: float = 0.0
    area_uncertainty_ha: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pixel_count": self.pixel_count,
            "area_m2": round(self.area_m2, 2),
            "area_ha": round(self.area_ha, 4),
            "area_uncertainty_m2": round(self.area_uncertainty_m2, 2),
            "area_uncertainty_ha": round(self.area_uncertainty_ha, 4),
            "perimeter_m": round(self.perimeter_m, 2),
            "centroid": self.centroid,
            "bbox": self.bbox,
            "geometry": self.geometry,
            "index_method": self.index_method,
            "threshold": round(self.threshold, 3),
            "valid_pixel_fraction": round(self.valid_pixel_fraction, 3),
            "spectral_mean": round(self.spectral_mean, 4),
        }


@dataclass
class WaterBodyAnalysisResult:
    """Complete output of deterministic water body analysis."""
    source_image_id: str
    raster_path: str
    crs: str
    resolution_m: float
    total_water_area_m2: float
    total_water_area_ha: float
    candidate_count: int
    candidates: List[WaterBodyCandidate]
    selected_candidate: Optional[WaterBodyCandidate]
    water_index_used: str
    threshold_applied: float
    threshold_method: str
    cloud_contamination_ratio: float
    valid_pixel_ratio: float
    evidence_decision: str  # "ANSWER", "QUALIFY", "ABSTAIN"
    decision_reason: str
    cloud_quality_info: Dict[str, Any] = field(default_factory=dict)
    is_ambiguous_largest: bool = False
    ambiguity_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_image_id": self.source_image_id,
            "raster_path": self.raster_path,
            "crs": self.crs,
            "resolution_m": self.resolution_m,
            "total_water_area_m2": round(self.total_water_area_m2, 2),
            "total_water_area_ha": round(self.total_water_area_ha, 4),
            "candidate_count": self.candidate_count,
            "candidates": [c.to_dict() for c in self.candidates],
            "selected_candidate": self.selected_candidate.to_dict() if self.selected_candidate else None,
            "water_index_used": self.water_index_used,
            "threshold_applied": round(self.threshold_applied, 3),
            "threshold_method": self.threshold_method,
            "cloud_contamination_ratio": round(self.cloud_contamination_ratio, 3),
            "valid_pixel_ratio": round(self.valid_pixel_ratio, 3),
            "evidence_decision": self.evidence_decision,
            "decision_reason": self.decision_reason,
            "cloud_quality_info": self.cloud_quality_info,
            "is_ambiguous_largest": self.is_ambiguous_largest,
            "ambiguity_details": self.ambiguity_details,
        }


class WaterBodyAnalyzer:
    """Scientific engine for deterministic water detection and spatial ranking."""

    def __init__(self, min_area_m2: float = 500.0, default_threshold: float = 0.0):
        self.min_area_m2 = min_area_m2
        self.default_threshold = default_threshold
        self.geod = pyproj.Geod(ellps="WGS84") if HAS_SHAPELY else None

    def analyze(
        self,
        raster_path: Path | str,
        image_id: str = "active_image",
        threshold_method: str = "adaptive",  # "fixed", "adaptive", "otsu"
    ) -> WaterBodyAnalysisResult:
        """Run end-to-end water body segmentation, polygonization, and ranking."""
        r_path = Path(raster_path)
        if not r_path.exists():
            raise FileNotFoundError(f"Raster file not found: {r_path}")

        if not HAS_RASTERIO or not HAS_SHAPELY:
            raise RuntimeError("rasterio and shapely are required for WaterBodyAnalyzer")

        with rasterio.open(r_path) as src:
            count = src.count
            width = src.width
            height = src.height
            crs = src.crs
            transform = src.transform
            nodata_val = src.nodata

            # Extract pixel resolution in meters
            res_x = abs(transform[0])
            res_y = abs(transform[4])
            pixel_area_m2 = res_x * res_y

            # 1. Band mapping
            # In standard 4-band S2: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
            # In standard 3-band: R, G, B
            # In 12-band S2 L2A: B03=Green, B08=NIR, B11=SWIR1
            green_band = None
            nir_band = None
            swir_band = None

            if count >= 11:
                green_band = src.read(3).astype(np.float32)
                nir_band = src.read(8).astype(np.float32)
                swir_band = src.read(11).astype(np.float32)
                index_method = "MNDWI"
            elif count >= 4:
                green_band = src.read(2).astype(np.float32)
                nir_band = src.read(4).astype(np.float32)
                index_method = "NDWI"
            elif count == 3:
                # RGB fallback: Green vs Red contrast
                red_band = src.read(1).astype(np.float32)
                green_band = src.read(2).astype(np.float32)
                nir_band = red_band
                index_method = "NDWI"
            else:
                # Single band
                arr = src.read(1).astype(np.float32)
                green_band = arr
                nir_band = arr * 0.5
                index_method = "NDWI"

            # 2. Mask invalid & nodata pixels
            valid_mask = np.ones((height, width), dtype=bool)
            if nodata_val is not None:
                valid_mask &= (green_band != nodata_val)
            valid_mask &= (green_band > 0)
            valid_pixel_count = int(np.sum(valid_mask))
            total_pixel_count = width * height
            valid_pixel_ratio = float(valid_pixel_count / total_pixel_count) if total_pixel_count > 0 else 0.0

            if valid_pixel_count == 0:
                return WaterBodyAnalysisResult(
                    source_image_id=image_id,
                    raster_path=str(r_path),
                    crs=str(crs),
                    resolution_m=res_x,
                    total_water_area_m2=0.0,
                    total_water_area_ha=0.0,
                    candidate_count=0,
                    candidates=[],
                    selected_candidate=None,
                    water_index_used=index_method,
                    threshold_applied=self.default_threshold,
                    threshold_method=threshold_method,
                    cloud_contamination_ratio=0.0,
                    valid_pixel_ratio=0.0,
                    evidence_decision="ABSTAIN",
                    decision_reason="No valid raster pixels available in observation.",
                )

            # Multi-tiered cloud detection via CloudQualityEstimator
            cloud_estimator = CloudQualityEstimator()
            cloud_res = cloud_estimator.estimate_from_dataset(src)
            cloud_ratio = cloud_res.cloud_fraction
            cloud_mask = (
                cloud_res.cloud_mask
                if cloud_res.cloud_mask is not None and cloud_res.cloud_mask.shape == (height, width)
                else np.zeros((height, width), dtype=bool)
            )
            cloud_info = cloud_res.to_dict()

            # 3. Calculate Water Index (MNDWI or NDWI)
            if index_method == "MNDWI" and swir_band is not None:
                denom = green_band + swir_band
                denom_safe = np.where(denom > 1e-6, denom, 1.0)
                water_index = np.where(denom > 1e-6, (green_band - swir_band) / denom_safe, -1.0)
            else:
                denom = green_band + nir_band
                denom_safe = np.where(denom > 1e-6, denom, 1.0)
                water_index = np.where(denom > 1e-6, (green_band - nir_band) / denom_safe, -1.0)

            water_index[~valid_mask] = -1.0
            water_index[cloud_mask] = -1.0

            # 4. Thresholding
            thresh = self.default_threshold
            if threshold_method == "otsu":
                valid_vals = water_index[valid_mask & ~cloud_mask]
                if len(valid_vals) > 100:
                    counts, bin_edges = np.histogram(valid_vals, bins=50)
                    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                    total = len(valid_vals)
                    current_max = 0
                    optimal_thresh = 0.0
                    weight_bg = 0
                    sum_bg = 0
                    sum_total = np.sum(bin_centers * counts)
                    for i in range(len(counts)):
                        weight_bg += counts[i]
                        if weight_bg == 0:
                            continue
                        weight_fg = total - weight_bg
                        if weight_fg == 0:
                            break
                        sum_bg += bin_centers[i] * counts[i]
                        mean_bg = sum_bg / weight_bg
                        mean_fg = (sum_total - sum_bg) / weight_fg
                        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
                        if between_var > current_max:
                            current_max = between_var
                            optimal_thresh = bin_centers[i]
                    thresh = float(max(-0.15, min(0.35, optimal_thresh)))
            elif threshold_method == "adaptive":
                valid_vals = water_index[valid_mask & ~cloud_mask]
                if len(valid_vals) > 0:
                    p75 = float(np.percentile(valid_vals, 75))
                    p90 = float(np.percentile(valid_vals, 90))
                    thresh = float(max(0.0, min(0.25, (p75 + p90) / 2)))

            raw_mask = (water_index > thresh) & valid_mask & ~cloud_mask

            # 5. Morphological cleaning
            if HAS_SCIPY:
                # Remove isolated speckles (opening) and fill small holes (closing)
                clean_mask = ndi.binary_opening(raw_mask, structure=np.ones((3, 3)))
                clean_mask = ndi.binary_closing(clean_mask, structure=np.ones((3, 3)))
                labeled_array, num_features = ndi.label(clean_mask)
            else:
                clean_mask = raw_mask
                labeled_array = clean_mask.astype(np.int32)
                num_features = 1 if np.any(clean_mask) else 0

            # 6. Extract candidate water bodies with genuine vector contours
            candidates: List[WaterBodyCandidate] = []
            total_water_area_m2 = 0.0

            for feat_idx in range(1, num_features + 1):
                comp_mask = (labeled_array == feat_idx).astype(np.uint8)
                px_count = int(np.sum(comp_mask))
                est_m2 = px_count * pixel_area_m2
                if est_m2 < self.min_area_m2:
                    continue  # Filter out sub-threshold noise

                # Extract exact vector contours for this component
                shapes_gen = rasterio.features.shapes(comp_mask, mask=comp_mask > 0, transform=transform)
                geoms = [shape(geom) for geom, val in shapes_gen if val == 1]
                if not geoms:
                    continue

                unified_geom = unary_union(geoms)
                if unified_geom.is_empty:
                    continue

                # Reproject to WGS84 (EPSG:4326) if native is projected
                if crs and crs.to_epsg() != 4326:
                    wgs84_geom_dict = transform_geom(crs, "EPSG:4326", mapping(unified_geom))
                    wgs84_poly = shape(wgs84_geom_dict)
                else:
                    wgs84_poly = unified_geom

                # Geodesic area & perimeter on WGS84 ellipsoid
                if self.geod and wgs84_poly.is_valid:
                    area_m2, perim_m = self.geod.geometry_area_perimeter(wgs84_poly)
                    area_m2 = abs(area_m2)
                    perim_m = abs(perim_m)
                else:
                    area_m2 = est_m2
                    perim_m = float(unified_geom.length)

                area_ha = area_m2 / 10000.0
                total_water_area_m2 += area_m2

                # Centroid in WGS84
                c_pt = wgs84_poly.centroid
                centroid = {"lat": round(float(c_pt.y), 6), "lon": round(float(c_pt.x), 6)}

                # Normalized bounding box in raster coords
                minx, miny, maxx, maxy = unified_geom.bounds
                # raster bounds
                r_bounds = src.bounds
                bbox_norm = {
                    "ymin": max(0.0, min(1.0, (r_bounds.top - maxy) / (r_bounds.top - r_bounds.bottom))),
                    "xmin": max(0.0, min(1.0, (minx - r_bounds.left) / (r_bounds.right - r_bounds.left))),
                    "ymax": max(0.0, min(1.0, (r_bounds.top - miny) / (r_bounds.top - r_bounds.bottom))),
                    "xmax": max(0.0, min(1.0, (maxx - r_bounds.left) / (r_bounds.right - r_bounds.left))),
                }

                # Simplify geometry slightly to keep payload clean
                simplified = wgs84_poly.simplify(tolerance=0.00005, preserve_topology=True)
                geo_json = mapping(simplified)

                # Mixed-pixel boundary uncertainty: approx 0.5 pixel width along perimeter
                uncertainty_m2 = perim_m * res_x * 0.5
                uncertainty_ha = uncertainty_m2 / 10000.0
                cand_spectral_mean = float(np.mean(water_index[comp_mask > 0])) if np.any(comp_mask > 0) else float(thresh)

                candidates.append(
                    WaterBodyCandidate(
                        id=f"water_body_{len(candidates) + 1:02d}",
                        pixel_count=px_count,
                        area_m2=area_m2,
                        area_ha=area_ha,
                        area_uncertainty_m2=uncertainty_m2,
                        area_uncertainty_ha=uncertainty_ha,
                        perimeter_m=perim_m,
                        centroid=centroid,
                        bbox=bbox_norm,
                        geometry=geo_json,
                        index_method=index_method,
                        threshold=thresh,
                        valid_pixel_fraction=valid_pixel_ratio,
                        spectral_mean=cand_spectral_mean,
                    )
                )

            # 7. Sort candidates by area descending
            candidates.sort(key=lambda c: c.area_m2, reverse=True)
            selected = candidates[0] if candidates else None

            # Statistical ambiguity check between rank 1 and rank 2
            is_ambiguous = False
            ambiguity_info = None
            if len(candidates) >= 2:
                c1 = candidates[0]
                c2 = candidates[1]
                delta_m2 = c1.area_m2 - c2.area_m2
                sigma_diff_m2 = float(np.sqrt(c1.area_uncertainty_m2**2 + c2.area_uncertainty_m2**2))
                if delta_m2 <= sigma_diff_m2:
                    is_ambiguous = True
                    ambiguity_info = {
                        "candidate_1_id": c1.id,
                        "candidate_2_id": c2.id,
                        "area_1_ha": round(c1.area_ha, 2),
                        "area_2_ha": round(c2.area_ha, 2),
                        "difference_ha": round(abs(c1.area_ha - c2.area_ha), 4),
                        "uncertainty_margin_ha": round(sigma_diff_m2 / 10000.0, 4),
                        "statistical_status": "indistinguishable_at_current_gsd",
                    }

            # 8. Evidence Gate Decision
            if not candidates:
                decision = "ABSTAIN"
                reason = "No coherent water bodies exceeding the minimum area threshold (500 m²) were detected in the observation."
            elif is_ambiguous and ambiguity_info:
                decision = "QUALIFY"
                reason = (
                    f"Two water bodies have statistically indistinguishable measured areas "
                    f"({candidates[0].area_ha:.2f} ha vs {candidates[1].area_ha:.2f} ha, "
                    f"difference {ambiguity_info['difference_ha']:.2f} ha <= "
                    f"{ambiguity_info['uncertainty_margin_ha']:.2f} ha measurement uncertainty) "
                    f"at current observation quality."
                )
            elif cloud_ratio > 0.35:
                decision = "QUALIFY"
                cloud_m = cloud_info.get("method", "cloud_estimator")
                reason = f"Water body detected, but high cloud contamination ({cloud_ratio * 100:.1f}%, evaluated via {cloud_m}) reduces boundary certainty."
            elif valid_pixel_ratio < 0.60:
                decision = "QUALIFY"
                reason = f"Limited valid pixel coverage ({valid_pixel_ratio * 100:.1f}%) in scene bounds."
            else:
                decision = "ANSWER"
                reason = f"Conclusively identified {len(candidates)} water body candidate(s) with clear spectral signature."

            return WaterBodyAnalysisResult(
                source_image_id=image_id,
                raster_path=str(r_path),
                crs=str(crs.to_string() if crs else "Local"),
                resolution_m=res_x,
                total_water_area_m2=total_water_area_m2,
                total_water_area_ha=total_water_area_m2 / 10000.0,
                candidate_count=len(candidates),
                candidates=candidates,
                selected_candidate=selected,
                water_index_used=index_method,
                threshold_applied=thresh,
                threshold_method=threshold_method,
                cloud_contamination_ratio=cloud_ratio,
                valid_pixel_ratio=valid_pixel_ratio,
                evidence_decision=decision,
                decision_reason=reason,
                cloud_quality_info=cloud_info,
                is_ambiguous_largest=is_ambiguous,
                ambiguity_details=ambiguity_info,
            )


water_body_analyzer = WaterBodyAnalyzer()
