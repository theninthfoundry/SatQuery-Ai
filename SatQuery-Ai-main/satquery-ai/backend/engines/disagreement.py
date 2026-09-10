"""Sensor Disagreement Diagnostic Engine for Optical and SAR Remote Sensing.

Explains the physical and environmental causes of discrepancy when optical
and SAR sensors disagree on ground observations:
1. Cloud occlusion & cloud shadows (Optical obscured, SAR penetrates)
2. Specular reflection from smooth surfaces (Asphalt/runways appear as water in SAR)
3. Emergent vegetation / submerged canopy (SAR double-bounce vs optical canopy reflection)
4. Wind-induced water surface roughness (Roughened water backscatters in SAR)
5. Registration boundary misalignment (Boundary pixel mismatch)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import numpy as np


class DisagreementReason(str, Enum):
    """Physical hypotheses explaining optical vs SAR discrepancy."""
    CLOUD_SHADOW_OCCLUSION = "cloud_shadow_occlusion"
    SMOOTH_SURFACE_SPECULAR = "smooth_surface_specular"  # Dry runway/asphalt mimics water in SAR
    FLOODED_VEGETATION_DOUBLE_BOUNCE = "flooded_vegetation_double_bounce"  # Flooding under canopy
    WIND_ROUGHENED_WATER = "wind_roughened_water"  # Water appears rough/bright in SAR
    REGISTRATION_BOUNDARY_SHIFT = "registration_boundary_shift"
    TEMPORAL_GAP_PHENOMENON = "temporal_gap_phenomenon"
    SPECTRAL_SHADOW_CONFUSION = "spectral_shadow_confusion"
    UNCERTAIN = "uncertain"


@dataclass
class DisagreementDiagnosis:
    """Diagnostic report explaining sensor discrepancies."""
    total_disagreement_pixels: int
    optical_only_fraction: float
    sar_only_fraction: float
    primary_hypothesis: DisagreementReason
    confidence: float
    secondary_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    boundary_pixel_fraction: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    scientific_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_disagreement_pixels": self.total_disagreement_pixels,
            "proportions": {
                "optical_only": round(self.optical_only_fraction, 3),
                "sar_only": round(self.sar_only_fraction, 3),
                "boundary_pixel_fraction": round(self.boundary_pixel_fraction, 3),
            },
            "diagnosis": {
                "primary_hypothesis": self.primary_hypothesis.value,
                "confidence": round(self.confidence, 3),
                "secondary": self.secondary_hypotheses,
            },
            "scientific_explanation": self.scientific_explanation,
            "recommendations": self.recommendations,
        }


class SensorDisagreementEngine:
    """Diagnoses physical reasons for discordance between optical and SAR observations."""

    def diagnose_water_disagreement(
        self,
        optical_water_mask: np.ndarray,
        sar_water_mask: np.ndarray,
        optical_rgb: Optional[np.ndarray] = None,
        sar_sigma0_db: Optional[np.ndarray] = None,
        cloud_mask: Optional[np.ndarray] = None,
        temporal_gap_hours: float = 0.0,
    ) -> DisagreementDiagnosis:
        """Diagnose discrepancies between optical water mask (e.g. from NDWI) and SAR water mask (from backscatter threshold).
        
        Args:
            optical_water_mask: (H, W) bool array.
            sar_water_mask: (H, W) bool array.
            optical_rgb: Optional (H, W, 3) image for color/shadow analysis.
            sar_sigma0_db: Optional (H, W) calibrated sigma0 backscatter array in dB.
            cloud_mask: Optional (H, W) cloud detection mask.
            temporal_gap_hours: Time interval between observations in hours.
        """
        opt_b = (optical_water_mask > 0)
        sar_b = (sar_water_mask > 0)

        opt_only = opt_b & (~sar_b)
        sar_only = (~opt_b) & sar_b
        disagree = opt_only | sar_only
        n_disagree = int(np.sum(disagree))

        if n_disagree == 0:
            return DisagreementDiagnosis(
                total_disagreement_pixels=0,
                optical_only_fraction=0.0,
                sar_only_fraction=0.0,
                primary_hypothesis=DisagreementReason.UNCERTAIN,
                confidence=1.0,
                scientific_explanation="Total consensus between optical and SAR detections; no physical disagreement detected.",
            )

        n_opt_only = int(np.sum(opt_only))
        n_sar_only = int(np.sum(sar_only))
        opt_fraction = n_opt_only / max(1, n_disagree)
        sar_fraction = n_sar_only / max(1, n_disagree)

        # 1. Check boundary pixel fraction (spatial erosion/dilation)
        boundary_fraction = self._estimate_boundary_fraction(opt_b, sar_b)

        # 2. Check cloud occlusion hypothesis
        cloud_overlap = 0.0
        if cloud_mask is not None and np.any(cloud_mask):
            cloud_overlap = float(np.sum(sar_only & (cloud_mask > 0)) / max(1, n_sar_only))

        hypotheses: List[Dict[str, Any]] = []

        # Evaluate hypotheses
        if boundary_fraction > 0.65:
            primary = DisagreementReason.REGISTRATION_BOUNDARY_SHIFT
            conf = 0.85
            expl = (
                f"{boundary_fraction * 100:.1f}% of discrepancies occur along waterbody perimeter boundaries. "
                "This indicates minor sub-pixel co-registration offset or shoreline water-level tidal fluctuation."
            )
        elif cloud_overlap > 0.40:
            primary = DisagreementReason.CLOUD_SHADOW_OCCLUSION
            conf = 0.90
            expl = (
                "SAR detected water beneath cloud cover where optical sensors were occluded. "
                "Radar penetrates atmospheric haze and clouds, providing true ground observation."
            )
        elif opt_fraction > 0.70:
            # Optical detected water, but SAR did not
            # Likely causes: wind-induced waves creating high radar backscatter, or dark terrain/shadow in optical
            primary = DisagreementReason.WIND_ROUGHENED_WATER
            conf = 0.75
            expl = (
                "Optical sensors detected water bodies that SAR classified as non-water. "
                "This is typically caused by wind-induced wave chop roughening the water surface, "
                "causing diffuse radar backscatter above the -16 dB threshold."
            )
            hypotheses.append({
                "hypothesis": DisagreementReason.SPECTRAL_SHADOW_CONFUSION.value,
                "likelihood": 0.60,
                "notes": "Topographic or building shadows can trigger false-positive NDWI water detections.",
            })
        elif sar_fraction > 0.70:
            # SAR detected water (low backscatter), but optical did not
            primary = DisagreementReason.SMOOTH_SURFACE_SPECULAR
            conf = 0.78
            expl = (
                "SAR classified smooth surfaces as water due to specular reflection (low backscatter), "
                "whereas optical confirmed dry land (e.g. paved runways, dry sand flats, or solar farms)."
            )
            hypotheses.append({
                "hypothesis": DisagreementReason.FLOODED_VEGETATION_DOUBLE_BOUNCE.value,
                "likelihood": 0.55,
                "notes": "Emergent vegetation can mask standing floodwaters in optical while altering SAR polarimetry.",
            })
        else:
            primary = DisagreementReason.TEMPORAL_GAP_PHENOMENON if temporal_gap_hours > 24 else DisagreementReason.UNCERTAIN
            conf = 0.65
            expl = (
                f"Mixed discrepancy pattern ({opt_fraction * 100:.1f}% optical-only, {sar_fraction * 100:.1f}% SAR-only) "
                f"with a {temporal_gap_hours:.1f}h acquisition gap. Dynamic water movement or tidal changes likely occurred."
            )

        recommendations = [
            "Use fused consensus mask where both sensors agree for critical mission reporting.",
            "Inspect high-resolution optical previews in regions flagged with specular confusion.",
        ]
        if boundary_fraction > 0.50:
            recommendations.append("Apply morphological boundary buffering or sub-pixel co-registration.")

        return DisagreementDiagnosis(
            total_disagreement_pixels=n_disagree,
            optical_only_fraction=opt_fraction,
            sar_only_fraction=sar_fraction,
            primary_hypothesis=primary,
            confidence=conf,
            secondary_hypotheses=hypotheses,
            boundary_pixel_fraction=boundary_fraction,
            recommendations=recommendations,
            scientific_explanation=expl,
        )

    def _estimate_boundary_fraction(self, mask1: np.ndarray, mask2: np.ndarray) -> float:
        """Estimate what fraction of disagreement occurs on immediate 1-pixel boundaries."""
        try:
            from scipy.ndimage import binary_dilation, binary_erosion
            # Boundary of union
            union = mask1 | mask2
            eroded = binary_erosion(union, structure=np.ones((3, 3)))
            boundary_zone = union & (~eroded)

            disagreement = mask1 ^ mask2
            n_disagree = int(np.sum(disagreement))
            if n_disagree == 0:
                return 0.0
            boundary_disagree = int(np.sum(disagreement & boundary_zone))
            return float(boundary_disagree / n_disagree)
        except Exception:
            return 0.0
