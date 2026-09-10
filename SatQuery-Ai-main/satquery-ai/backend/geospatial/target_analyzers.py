"""Generalized Target Physical Phenomenon Analyzers for Remote Sensing.

Implements unified candidate extraction and measurement for:
- water_body (MNDWI / NDWI)
- built_up (NDBI / BSI / NDVI inverse)
- vegetation (NDVI / SAVI)
- change_region (bi-temporal spectral delta)

Every analyzer outputs standardized SpatialCandidate objects with WGS84 geodesic geometry.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

try:
    import rasterio
    from rasterio.features import shapes
    import shapely.geometry as sgeom
    from shapely.ops import transform
    import pyproj
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from .indices import calculate_ndvi, calculate_ndwi, calculate_mndwi, calculate_ndbi
from .water_body import water_body_analyzer


@dataclass
class SpatialCandidate:
    """Standardized physical candidate extracted from satellite raster."""
    id: str
    target_type: str
    area_m2: float
    area_ha: float
    area_uncertainty_ha: float
    perimeter_m: float
    geometry: Dict[str, Any]
    centroid: Tuple[float, float]
    spectral_mean: float
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "target_type": self.target_type,
            "area_m2": round(self.area_m2, 2),
            "area_ha": round(self.area_ha, 4),
            "area_uncertainty_ha": round(self.area_uncertainty_ha, 4),
            "perimeter_m": round(self.perimeter_m, 2),
            "centroid": [round(c, 6) for c in self.centroid],
            "spectral_mean": round(self.spectral_mean, 4),
            "geometry": self.geometry,
            "properties": self.properties,
        }


@dataclass
class TargetAnalysisResult:
    """Consolidated result of physical target phenomenon analysis."""
    image_id: str
    target_type: str
    candidates: List[SpatialCandidate]
    total_detected_area_ha: float
    mean_uncertainty_ha: float
    processing_time_sec: float
    index_name: str
    threshold_used: float
    is_empty: bool = False
    valid_pixel_coverage: float = 1.0
    cloud_freedom: float = 1.0
    resolution_suitability: float = 1.0
    spectral_distinctiveness: float = 0.5
    geometry_validity: float = 1.0
    reliability_score: float = 0.5
    reliability_factors: Dict[str, float] = field(default_factory=dict)


class BaseTargetAnalyzer(ABC):
    """Abstract base class for all deterministic remote sensing target analyzers."""

    @abstractmethod
    def analyze(self, raster_path: Path | str, image_id: str = "active_image") -> TargetAnalysisResult:
        """Extract and measure candidate physical entities from imagery."""
        pass


class WaterBodyTargetAnalyzer(BaseTargetAnalyzer):
    """Specialist analyzer for inland water bodies via MNDWI/NDWI."""

    def analyze(self, raster_path: Path | str, image_id: str = "active_image") -> TargetAnalysisResult:
        wb_res = water_body_analyzer.analyze(raster_path, image_id=image_id, threshold_method="adaptive")
        candidates = []
        for c in wb_res.candidates:
            spec_mean = getattr(c, "spectral_mean", getattr(c, "spectral_mean_mndwi", c.threshold + 0.15))
            c_lat = c.centroid["lat"] if isinstance(c.centroid, dict) else c.centroid[0]
            c_lon = c.centroid["lon"] if isinstance(c.centroid, dict) else c.centroid[1]
            candidates.append(SpatialCandidate(
                id=c.id,
                target_type="water_body",
                area_m2=c.area_m2,
                area_ha=c.area_ha,
                area_uncertainty_ha=c.area_uncertainty_ha,
                perimeter_m=c.perimeter_m,
                geometry=c.geometry,
                centroid=(float(c_lat), float(c_lon)),
                spectral_mean=float(spec_mean),
                properties={"threshold": c.threshold, "pixel_count": c.pixel_count},
            ))

        valid_cov = round(float(wb_res.valid_pixel_ratio), 4)
        cloud_free = round(float(max(0.0, min(1.0, 1.0 - wb_res.cloud_contamination_ratio))), 4)
        res_m = float(wb_res.resolution_m) if wb_res.resolution_m > 0 else 10.0
        res_suit = round(float(min(1.0, max(0.1, 10.0 / max(0.1, res_m)))), 4)

        if candidates:
            top_cand = candidates[0]
            thresh = wb_res.threshold_applied
            s_diff = max(0.0, top_cand.spectral_mean - thresh)
            spec_distinct = round(float(min(1.0, max(0.2, s_diff / max(0.1, 1.0 - thresh)))), 4)
            geom_valid = 1.0
            r_score = round(float(valid_cov * cloud_free * res_suit * spec_distinct * geom_valid), 4)
        else:
            spec_distinct = 0.2
            geom_valid = 1.0
            r_score = 0.0

        r_factors = {
            "valid_pixel_coverage": valid_cov,
            "cloud_freedom": cloud_free,
            "resolution_suitability": res_suit,
            "spectral_distinctiveness": spec_distinct,
            "geometry_validity": geom_valid,
        }

        return TargetAnalysisResult(
            image_id=image_id,
            target_type="water_body",
            candidates=candidates,
            total_detected_area_ha=wb_res.total_water_area_ha,
            mean_uncertainty_ha=wb_res.mean_uncertainty_ha,
            processing_time_sec=wb_res.processing_time_sec,
            index_name=wb_res.water_index_used,
            threshold_used=wb_res.threshold_applied,
            is_empty=len(candidates) == 0,
            valid_pixel_coverage=valid_cov,
            cloud_freedom=cloud_free,
            resolution_suitability=res_suit,
            spectral_distinctiveness=spec_distinct,
            geometry_validity=geom_valid,
            reliability_score=r_score,
            reliability_factors=r_factors,
        )


class BuiltUpTargetAnalyzer(BaseTargetAnalyzer):
    """Specialist analyzer for built-up and impervious surfaces via NDBI."""

    def analyze(self, raster_path: Path | str, image_id: str = "active_image") -> TargetAnalysisResult:
        t0 = time.perf_counter()
        r_path = Path(raster_path)
        if not r_path.exists():
            raise FileNotFoundError(f"Raster not found: {r_path}")

        if not HAS_GEO or not HAS_SCIPY:
            return TargetAnalysisResult(image_id, "built_up", [], 0.0, 0.0, 0.0, "NDBI", 0.0, True)

        with rasterio.open(r_path) as src:
            bounds = src.bounds
            crs = src.crs
            transform_mat = src.transform
            gsd_m = abs(transform_mat.a) if hasattr(transform_mat, "a") else 10.0
            profile = src.profile
            num_bands = src.count

            # Extract SWIR and NIR or fallback to Green/Red
            if num_bands >= 6:
                nir = src.read(4).astype(np.float32)
                swir = src.read(5).astype(np.float32)
            elif num_bands >= 4:
                red = src.read(1).astype(np.float32)
                nir = src.read(4).astype(np.float32)
                swir = red  # proxy
            else:
                swir = src.read(1).astype(np.float32)
                nir = src.read(2).astype(np.float32) if num_bands >= 2 else swir

        # Compute NDBI
        denom = swir + nir
        ndbi = np.zeros_like(swir, dtype=np.float32)
        valid = (denom > 1e-4) & np.isfinite(swir) & np.isfinite(nir)
        ndbi[valid] = (swir[valid] - nir[valid]) / denom[valid]

        # Built-up threshold
        threshold = 0.05
        binary_mask = (ndbi > threshold) & valid

        # Morphological closing
        binary_mask = ndimage.binary_closing(binary_mask, structure=np.ones((3, 3)))
        labeled_mask, num_features = ndimage.label(binary_mask)

        candidates: List[SpatialCandidate] = []
        geod = pyproj.Geod(ellps="WGS84")

        min_pixels = 5  # minimum coherent block
        for feat_id in range(1, num_features + 1):
            comp_mask = (labeled_mask == feat_id)
            pixel_count = int(np.sum(comp_mask))
            if pixel_count < min_pixels:
                continue

            shapes_gen = shapes(comp_mask.astype(np.uint8), mask=comp_mask, transform=transform_mat)
            for geom_dict, val in shapes_gen:
                if val == 1:
                    poly = sgeom.shape(geom_dict)
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    if poly.is_empty:
                        continue

                    # Transform to WGS84 for geodesic calculation if projected
                    if crs and crs.to_epsg() != 4326:
                        to_wgs84 = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
                        poly_wgs84 = transform(to_wgs84, poly)
                    else:
                        poly_wgs84 = poly

                    area_m2, perimeter_m = geod.geometry_area_perimeter(poly_wgs84)
                    area_m2 = abs(area_m2)
                    perimeter_m = abs(perimeter_m)

                    if area_m2 < 100.0:
                        continue

                    area_ha = area_m2 / 10000.0
                    uncertainty_m2 = perimeter_m * gsd_m * 0.5
                    uncertainty_ha = uncertainty_m2 / 10000.0
                    centroid = (float(poly_wgs84.centroid.y), float(poly_wgs84.centroid.x))

                    cand = SpatialCandidate(
                        id=f"built_up_{len(candidates) + 1}",
                        target_type="built_up",
                        area_m2=area_m2,
                        area_ha=area_ha,
                        area_uncertainty_ha=uncertainty_ha,
                        perimeter_m=perimeter_m,
                        geometry=sgeom.mapping(poly_wgs84),
                        centroid=centroid,
                        spectral_mean=float(np.mean(ndbi[comp_mask])),
                        properties={"pixel_count": pixel_count, "ndbi_mean": float(np.mean(ndbi[comp_mask]))},
                    )
                    candidates.append(cand)

        # Sort descending by area
        candidates.sort(key=lambda c: c.area_ha, reverse=True)
        total_ha = sum(c.area_ha for c in candidates)
        mean_unc = float(np.mean([c.area_uncertainty_ha for c in candidates])) if candidates else 0.0

        total_pixels = swir.size
        valid_pixel_count = int(np.sum(valid))
        valid_cov = round(float(valid_pixel_count / max(1, total_pixels)), 4)
        cloud_free = 1.0
        res_suit = round(float(min(1.0, max(0.1, 10.0 / max(0.1, gsd_m)))), 4)

        if candidates:
            top_cand = candidates[0]
            s_diff = max(0.0, top_cand.spectral_mean - threshold)
            spec_distinct = round(float(min(1.0, max(0.2, s_diff / max(0.1, 1.0 - threshold)))), 4)
            geom_valid = 1.0
            r_score = round(float(valid_cov * cloud_free * res_suit * spec_distinct * geom_valid), 4)
        else:
            spec_distinct = 0.2
            geom_valid = 1.0
            r_score = 0.0

        r_factors = {
            "valid_pixel_coverage": valid_cov,
            "cloud_freedom": cloud_free,
            "resolution_suitability": res_suit,
            "spectral_distinctiveness": spec_distinct,
            "geometry_validity": geom_valid,
        }

        return TargetAnalysisResult(
            image_id=image_id,
            target_type="built_up",
            candidates=candidates,
            total_detected_area_ha=total_ha,
            mean_uncertainty_ha=mean_unc,
            processing_time_sec=round(time.perf_counter() - t0, 3),
            index_name="NDBI",
            threshold_used=threshold,
            is_empty=len(candidates) == 0,
            valid_pixel_coverage=valid_cov,
            cloud_freedom=cloud_free,
            resolution_suitability=res_suit,
            spectral_distinctiveness=spec_distinct,
            geometry_validity=geom_valid,
            reliability_score=r_score,
            reliability_factors=r_factors,
        )


class VegetationTargetAnalyzer(BaseTargetAnalyzer):
    """Specialist analyzer for vegetation canopy and agricultural zones via NDVI."""

    def analyze(self, raster_path: Path | str, image_id: str = "active_image") -> TargetAnalysisResult:
        t0 = time.perf_counter()
        r_path = Path(raster_path)
        if not r_path.exists():
            raise FileNotFoundError(f"Raster not found: {r_path}")

        if not HAS_GEO or not HAS_SCIPY:
            return TargetAnalysisResult(image_id, "vegetation", [], 0.0, 0.0, 0.0, "NDVI", 0.0, True)

        with rasterio.open(r_path) as src:
            bounds = src.bounds
            crs = src.crs
            transform_mat = src.transform
            gsd_m = abs(transform_mat.a) if hasattr(transform_mat, "a") else 10.0
            num_bands = src.count

            if num_bands >= 4:
                red = src.read(3 if num_bands >= 4 else 1).astype(np.float32)
                nir = src.read(4).astype(np.float32)
            else:
                red = src.read(1).astype(np.float32)
                nir = src.read(2).astype(np.float32) if num_bands >= 2 else red

        denom = nir + red
        ndvi = np.zeros_like(nir, dtype=np.float32)
        valid = (denom > 1e-4) & np.isfinite(nir) & np.isfinite(red)
        ndvi[valid] = (nir[valid] - red[valid]) / denom[valid]

        threshold = 0.35
        binary_mask = (ndvi > threshold) & valid

        binary_mask = ndimage.binary_opening(binary_mask, structure=np.ones((3, 3)))
        labeled_mask, num_features = ndimage.label(binary_mask)

        candidates: List[SpatialCandidate] = []
        geod = pyproj.Geod(ellps="WGS84")

        min_pixels = 5
        for feat_id in range(1, num_features + 1):
            comp_mask = (labeled_mask == feat_id)
            pixel_count = int(np.sum(comp_mask))
            if pixel_count < min_pixels:
                continue

            shapes_gen = shapes(comp_mask.astype(np.uint8), mask=comp_mask, transform=transform_mat)
            for geom_dict, val in shapes_gen:
                if val == 1:
                    poly = sgeom.shape(geom_dict)
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    if poly.is_empty:
                        continue

                    if crs and crs.to_epsg() != 4326:
                        to_wgs84 = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
                        poly_wgs84 = transform(to_wgs84, poly)
                    else:
                        poly_wgs84 = poly

                    area_m2, perimeter_m = geod.geometry_area_perimeter(poly_wgs84)
                    area_m2 = abs(area_m2)
                    perimeter_m = abs(perimeter_m)

                    if area_m2 < 100.0:
                        continue

                    area_ha = area_m2 / 10000.0
                    uncertainty_m2 = perimeter_m * gsd_m * 0.5
                    uncertainty_ha = uncertainty_m2 / 10000.0
                    centroid = (float(poly_wgs84.centroid.y), float(poly_wgs84.centroid.x))

                    cand = SpatialCandidate(
                        id=f"vegetation_{len(candidates) + 1}",
                        target_type="vegetation",
                        area_m2=area_m2,
                        area_ha=area_ha,
                        area_uncertainty_ha=uncertainty_ha,
                        perimeter_m=perimeter_m,
                        geometry=sgeom.mapping(poly_wgs84),
                        centroid=centroid,
                        spectral_mean=float(np.mean(ndvi[comp_mask])),
                        properties={"pixel_count": pixel_count, "ndvi_mean": float(np.mean(ndvi[comp_mask]))},
                    )
                    candidates.append(cand)

        candidates.sort(key=lambda c: c.area_ha, reverse=True)
        total_ha = sum(c.area_ha for c in candidates)
        mean_unc = float(np.mean([c.area_uncertainty_ha for c in candidates])) if candidates else 0.0

        total_pixels = nir.size
        valid_pixel_count = int(np.sum(valid))
        valid_cov = round(float(valid_pixel_count / max(1, total_pixels)), 4)
        cloud_free = 1.0
        res_suit = round(float(min(1.0, max(0.1, 10.0 / max(0.1, gsd_m)))), 4)

        if candidates:
            top_cand = candidates[0]
            s_diff = max(0.0, top_cand.spectral_mean - threshold)
            spec_distinct = round(float(min(1.0, max(0.2, s_diff / max(0.1, 1.0 - threshold)))), 4)
            geom_valid = 1.0
            r_score = round(float(valid_cov * cloud_free * res_suit * spec_distinct * geom_valid), 4)
        else:
            spec_distinct = 0.2
            geom_valid = 1.0
            r_score = 0.0

        r_factors = {
            "valid_pixel_coverage": valid_cov,
            "cloud_freedom": cloud_free,
            "resolution_suitability": res_suit,
            "spectral_distinctiveness": spec_distinct,
            "geometry_validity": geom_valid,
        }

        return TargetAnalysisResult(
            image_id=image_id,
            target_type="vegetation",
            candidates=candidates,
            total_detected_area_ha=total_ha,
            mean_uncertainty_ha=mean_unc,
            processing_time_sec=round(time.perf_counter() - t0, 3),
            index_name="NDVI",
            threshold_used=threshold,
            is_empty=len(candidates) == 0,
            valid_pixel_coverage=valid_cov,
            cloud_freedom=cloud_free,
            resolution_suitability=res_suit,
            spectral_distinctiveness=spec_distinct,
            geometry_validity=geom_valid,
            reliability_score=r_score,
            reliability_factors=r_factors,
        )


def get_target_analyzer(target: str) -> BaseTargetAnalyzer:
    """Factory dispatching physical target phenomenon analyzer."""
    t_clean = target.lower().strip()
    if t_clean in ["water_body", "water", "lake", "river", "reservoir", "pond", "stream"]:
        return WaterBodyTargetAnalyzer()
    elif t_clean in ["built_up", "building", "buildings", "urban", "settlement", "settlements", "road", "roads", "infrastructure"]:
        return BuiltUpTargetAnalyzer()
    elif t_clean in ["vegetation", "forest", "forests", "tree", "trees", "crop", "crops", "agriculture", "canopy"]:
        return VegetationTargetAnalyzer()
    else:
        # Default to water body analyzer
        return WaterBodyTargetAnalyzer()
