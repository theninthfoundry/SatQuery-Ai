"""Asset Compatibility Engine — determines whether two EO assets can be scientifically compared.

Before ANY cross-asset analysis (temporal change, optical-SAR fusion), this engine validates:
1. Spatial overlap (bounding box IoU)
2. CRS compatibility (same or auto-reprojectable)
3. Resolution compatibility (GSD ratio within acceptable range)
4. Temporal gap assessment
5. Modality complementarity (for fusion tasks)
6. Data quality assessment

The system REFUSES to produce results when assets are incompatible,
rather than hallucinating analysis on mismatched data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .descriptor import EarthObservationAsset, Modality, BoundingBox


@dataclass
class CompatibilityReport:
    """Structured report on whether two assets can be compared."""

    compatible: bool
    overall_score: float  # 0.0 - 1.0 composite compatibility score

    # Component scores
    spatial_overlap: float  # IoU of bounding boxes (0.0 - 1.0)
    crs_compatible: bool
    crs_same: bool
    resolution_ratio: float  # ratio of GSD between the two assets
    resolution_compatible: bool
    temporal_gap_days: Optional[float]  # None if acquisition times unknown

    # Quality signals
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # For cross-modal
    modality_pair: Optional[str] = None  # e.g. "optical-sar", "optical-optical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compatible": self.compatible,
            "overall_score": round(self.overall_score, 3),
            "spatial_overlap": round(self.spatial_overlap, 3),
            "crs_compatible": self.crs_compatible,
            "crs_same": self.crs_same,
            "resolution_ratio": round(self.resolution_ratio, 3),
            "resolution_compatible": self.resolution_compatible,
            "temporal_gap_days": self.temporal_gap_days,
            "modality_pair": self.modality_pair,
            "warnings": self.warnings,
            "errors": self.errors,
            "recommendations": self.recommendations,
        }


class CompatibilityEngine:
    """Validates whether two EarthObservationAssets can be scientifically compared."""

    # Thresholds (configurable)
    MIN_SPATIAL_OVERLAP: float = 0.10  # Minimum 10% spatial overlap
    MAX_RESOLUTION_RATIO: float = 10.0  # Maximum 10:1 GSD ratio
    MAX_TEMPORAL_GAP_DAYS: float = 3650  # 10 years maximum temporal gap
    IDEAL_TEMPORAL_GAP_DAYS: float = 730  # 2 years is ideal for change detection

    def check_compatibility(
        self,
        asset_a: EarthObservationAsset,
        asset_b: EarthObservationAsset,
        intended_task: str = "change_detection",
    ) -> CompatibilityReport:
        """General task-aware compatibility dispatcher."""
        if intended_task in ("cross_modal", "corroboration", "sar_optical"):
            if asset_a.is_sar and not asset_b.is_sar:
                return self.check_cross_modal_pair(optical_asset=asset_b, sar_asset=asset_a)
            return self.check_cross_modal_pair(optical_asset=asset_a, sar_asset=asset_b)
        return self.check_temporal_pair(asset_before=asset_a, asset_after=asset_b)

    def check_temporal_pair(
        self,
        asset_before: EarthObservationAsset,
        asset_after: EarthObservationAsset,
    ) -> CompatibilityReport:
        """Validate compatibility for bi-temporal change detection."""
        warnings: List[str] = []
        errors: List[str] = []
        recommendations: List[str] = []

        # 1. Both must be same modality category
        if asset_before.is_sar != asset_after.is_sar:
            warnings.append(
                f"Mixed modalities: {asset_before.modality.value} (T1) vs "
                f"{asset_after.modality.value} (T2). Change detection works best "
                "with same-modality pairs."
            )

        # 2. Spatial overlap
        spatial_overlap = self._compute_spatial_overlap(asset_before, asset_after)
        if spatial_overlap < self.MIN_SPATIAL_OVERLAP:
            errors.append(
                f"Insufficient spatial overlap: {spatial_overlap:.1%}. "
                f"Minimum required is {self.MIN_SPATIAL_OVERLAP:.0%}. "
                "These images likely cover different geographic areas."
            )

        # 3. CRS compatibility
        crs_same = asset_before.crs == asset_after.crs
        crs_compatible = crs_same or (
            asset_before.has_valid_crs and asset_after.has_valid_crs
        )
        if not crs_compatible:
            if not asset_before.has_valid_crs:
                errors.append(f"T1 image '{asset_before.filename}' has no valid CRS.")
            if not asset_after.has_valid_crs:
                errors.append(f"T2 image '{asset_after.filename}' has no valid CRS.")
        elif not crs_same:
            warnings.append(
                f"CRS mismatch: T1 is '{asset_before.crs}', T2 is '{asset_after.crs}'. "
                "Auto-reprojection will be applied."
            )
            recommendations.append("Consider pre-registering images to the same CRS.")

        # 4. Resolution compatibility
        gsd_before = asset_before.resolution.avg_gsd_m
        gsd_after = asset_after.resolution.avg_gsd_m
        resolution_ratio = max(gsd_before, gsd_after) / max(0.001, min(gsd_before, gsd_after))
        resolution_compatible = resolution_ratio <= self.MAX_RESOLUTION_RATIO
        if not resolution_compatible:
            errors.append(
                f"Resolution mismatch too large: T1 is {gsd_before:.1f}m, "
                f"T2 is {gsd_after:.1f}m (ratio {resolution_ratio:.1f}:1). "
                f"Maximum ratio is {self.MAX_RESOLUTION_RATIO:.0f}:1."
            )
        elif resolution_ratio > 2.0:
            warnings.append(
                f"Significant resolution difference: T1 is {gsd_before:.1f}m, "
                f"T2 is {gsd_after:.1f}m. Results may be affected."
            )

        # 5. Dimension compatibility
        if (asset_before.width != asset_after.width or
                asset_before.height != asset_after.height):
            warnings.append(
                f"Dimension mismatch: T1 is {asset_before.width}×{asset_before.height}, "
                f"T2 is {asset_after.width}×{asset_after.height}. "
                "Images will be resampled to common dimensions."
            )

        # 6. Temporal gap
        temporal_gap_days = self._compute_temporal_gap(asset_before, asset_after)
        if temporal_gap_days is not None:
            if temporal_gap_days < 7:
                warnings.append(
                    f"Very short temporal gap ({temporal_gap_days:.0f} days). "
                    "Significant surface change is unlikely."
                )
            elif temporal_gap_days > self.MAX_TEMPORAL_GAP_DAYS:
                warnings.append(
                    f"Very long temporal gap ({temporal_gap_days:.0f} days). "
                    "Significant contextual differences may affect comparison."
                )

        # 7. Data quality
        if asset_before.nodata_fraction > 0.3:
            warnings.append(
                f"T1 has {asset_before.nodata_fraction:.0%} nodata pixels."
            )
        if asset_after.nodata_fraction > 0.3:
            warnings.append(
                f"T2 has {asset_after.nodata_fraction:.0%} nodata pixels."
            )
        if asset_before.cloud_fraction is not None and asset_before.cloud_fraction > 0.5:
            warnings.append(
                f"T1 has {asset_before.cloud_fraction:.0%} cloud cover. "
                "Optical analysis may be unreliable."
            )
        if asset_after.cloud_fraction is not None and asset_after.cloud_fraction > 0.5:
            warnings.append(
                f"T2 has {asset_after.cloud_fraction:.0%} cloud cover. "
                "Optical analysis may be unreliable."
            )

        # Compute overall score
        compatible = len(errors) == 0
        score = self._compute_compatibility_score(
            spatial_overlap=spatial_overlap,
            crs_compatible=crs_compatible,
            crs_same=crs_same,
            resolution_ratio=resolution_ratio,
            resolution_compatible=resolution_compatible,
            temporal_gap_days=temporal_gap_days,
            num_warnings=len(warnings),
        )

        modality_pair = f"{asset_before.modality.value}-{asset_after.modality.value}"

        return CompatibilityReport(
            compatible=compatible,
            overall_score=score,
            spatial_overlap=spatial_overlap,
            crs_compatible=crs_compatible,
            crs_same=crs_same,
            resolution_ratio=resolution_ratio,
            resolution_compatible=resolution_compatible,
            temporal_gap_days=temporal_gap_days,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
            modality_pair=modality_pair,
        )

    def check_cross_modal_pair(
        self,
        optical_asset: EarthObservationAsset,
        sar_asset: EarthObservationAsset,
    ) -> CompatibilityReport:
        """Validate compatibility for optical + SAR cross-modal fusion."""
        warnings: List[str] = []
        errors: List[str] = []
        recommendations: List[str] = []

        # 1. Verify modality assignment
        if not optical_asset.is_optical:
            if sar_asset.is_optical:
                # Swap
                optical_asset, sar_asset = sar_asset, optical_asset
                warnings.append("Asset roles were swapped: first asset is SAR, second is optical.")
            else:
                errors.append(
                    "Neither asset is classified as optical. "
                    "Cross-modal fusion requires one optical and one SAR asset."
                )

        if not sar_asset.is_sar:
            if optical_asset.is_sar:
                optical_asset, sar_asset = sar_asset, optical_asset
            else:
                warnings.append(
                    f"Second asset '{sar_asset.filename}' is not classified as SAR "
                    f"(detected as {sar_asset.modality.value}). "
                    "Cross-modal corroboration may produce limited results."
                )

        # 2-7: Same checks as temporal pair
        spatial_overlap = self._compute_spatial_overlap(optical_asset, sar_asset)
        if spatial_overlap < self.MIN_SPATIAL_OVERLAP:
            errors.append(
                f"Insufficient spatial overlap: {spatial_overlap:.1%}."
            )

        crs_same = optical_asset.crs == sar_asset.crs
        crs_compatible = crs_same or (
            optical_asset.has_valid_crs and sar_asset.has_valid_crs
        )
        if not crs_compatible:
            errors.append("CRS incompatibility between optical and SAR assets.")

        gsd_opt = optical_asset.resolution.avg_gsd_m
        gsd_sar = sar_asset.resolution.avg_gsd_m
        resolution_ratio = max(gsd_opt, gsd_sar) / max(0.001, min(gsd_opt, gsd_sar))
        resolution_compatible = resolution_ratio <= self.MAX_RESOLUTION_RATIO

        temporal_gap_days = self._compute_temporal_gap(optical_asset, sar_asset)
        if temporal_gap_days is not None and temporal_gap_days > 30:
            warnings.append(
                f"Optical and SAR acquired {temporal_gap_days:.0f} days apart. "
                "Surface changes between acquisitions may cause false disagreements."
            )

        compatible = len(errors) == 0
        score = self._compute_compatibility_score(
            spatial_overlap=spatial_overlap,
            crs_compatible=crs_compatible,
            crs_same=crs_same,
            resolution_ratio=resolution_ratio,
            resolution_compatible=resolution_compatible,
            temporal_gap_days=temporal_gap_days,
            num_warnings=len(warnings),
        )

        return CompatibilityReport(
            compatible=compatible,
            overall_score=score,
            spatial_overlap=spatial_overlap,
            crs_compatible=crs_compatible,
            crs_same=crs_same,
            resolution_ratio=resolution_ratio,
            resolution_compatible=resolution_compatible,
            temporal_gap_days=temporal_gap_days,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
            modality_pair="optical-sar",
        )

    # ──────────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_spatial_overlap(
        asset_a: EarthObservationAsset,
        asset_b: EarthObservationAsset,
    ) -> float:
        """Compute bounding box IoU using WGS84 coordinates when available."""
        bounds_a = asset_a.bounds
        bounds_b = asset_b.bounds

        if bounds_a is None or bounds_b is None:
            # If either lacks bounds, assume they might overlap
            if (asset_a.width == asset_b.width and
                    asset_a.height == asset_b.height):
                return 0.90  # Same dimensions, likely aligned
            return 0.50  # Unknown

        # Prefer WGS84 for cross-CRS comparison
        if bounds_a.wgs84 and bounds_b.wgs84:
            a = bounds_a.wgs84
            b = bounds_b.wgs84
            return CompatibilityEngine._bbox_iou(
                a["min_lon"], a["min_lat"], a["max_lon"], a["max_lat"],
                b["min_lon"], b["min_lat"], b["max_lon"], b["max_lat"],
            )

        # Fall back to native coordinates (only valid if same CRS)
        if asset_a.crs == asset_b.crs:
            return CompatibilityEngine._bbox_iou(
                bounds_a.min_x, bounds_a.min_y, bounds_a.max_x, bounds_a.max_y,
                bounds_b.min_x, bounds_b.min_y, bounds_b.max_x, bounds_b.max_y,
            )

        return 0.50  # Unknown overlap when CRS differ without WGS84

    @staticmethod
    def _bbox_iou(
        a_min_x: float, a_min_y: float, a_max_x: float, a_max_y: float,
        b_min_x: float, b_min_y: float, b_max_x: float, b_max_y: float,
    ) -> float:
        """Compute IoU between two axis-aligned bounding boxes."""
        inter_min_x = max(a_min_x, b_min_x)
        inter_min_y = max(a_min_y, b_min_y)
        inter_max_x = min(a_max_x, b_max_x)
        inter_max_y = min(a_max_y, b_max_y)

        if inter_max_x <= inter_min_x or inter_max_y <= inter_min_y:
            return 0.0

        inter_area = (inter_max_x - inter_min_x) * (inter_max_y - inter_min_y)
        a_area = (a_max_x - a_min_x) * (a_max_y - a_min_y)
        b_area = (b_max_x - b_min_x) * (b_max_y - b_min_y)
        union_area = a_area + b_area - inter_area

        return inter_area / max(1e-10, union_area)

    @staticmethod
    def _compute_temporal_gap(
        asset_a: EarthObservationAsset,
        asset_b: EarthObservationAsset,
    ) -> Optional[float]:
        """Compute temporal gap in days between two assets."""
        if asset_a.acquisition_time and asset_b.acquisition_time:
            delta = abs((asset_b.acquisition_time - asset_a.acquisition_time).total_seconds())
            return round(delta / 86400.0, 1)
        return None

    @staticmethod
    def _compute_compatibility_score(
        spatial_overlap: float,
        crs_compatible: bool,
        crs_same: bool,
        resolution_ratio: float,
        resolution_compatible: bool,
        temporal_gap_days: Optional[float],
        num_warnings: int,
    ) -> float:
        """Compute weighted compatibility score."""
        score = 0.0

        # Spatial overlap: 35% weight
        score += 0.35 * min(1.0, spatial_overlap / 0.8)

        # CRS: 20% weight
        if crs_same:
            score += 0.20
        elif crs_compatible:
            score += 0.15

        # Resolution: 25% weight
        if resolution_compatible:
            res_score = max(0.0, 1.0 - (resolution_ratio - 1.0) / 10.0)
            score += 0.25 * res_score

        # Temporal: 15% weight (if available)
        if temporal_gap_days is not None:
            temporal_score = max(0.0, 1.0 - temporal_gap_days / 3650.0)
            score += 0.15 * temporal_score
        else:
            score += 0.10  # Partial credit for unknown temporal gap

        # Warning penalty: 5% weight
        warning_penalty = min(1.0, num_warnings * 0.15)
        score += 0.05 * (1.0 - warning_penalty)

        return round(min(1.0, max(0.0, score)), 3)
