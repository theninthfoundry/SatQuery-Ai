"""Spatial cross-modal fusion engine for Optical and Synthetic Aperture Radar (SAR) data.

Implements true spatial, pixel-grounded fusion replacing heuristic scalar comparisons.
Provides:
1. Spatial intersection and mutual corroboration (agreement maps)
2. Modality-specific detection mapping (optical-only vs SAR-only)
3. Quantitative spatial overlap metrics (IoU, Dice, Cohen's Kappa)
4. Evidential consensus confidence modeling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


@dataclass
class FusionResult:
    """Quantitative result of spatial optical-SAR fusion."""
    task_name: str  # e.g., "water_body_detection", "urban_footprint", "flood_inundation"
    total_analyzed_pixels: int
    pixel_size_meters: Optional[float]

    # Spatial intersection metrics
    agreement_pixels: int
    optical_only_pixels: int
    sar_only_pixels: int
    neither_pixels: int

    # Overlap coefficients
    iou: float  # Intersection over Union
    dice_coefficient: float  # F1-score of agreement
    spatial_agreement_ratio: float  # agreement / (agreement + disagreements)
    cohens_kappa: float

    # Physical areas in square meters (if pixel size provided)
    agreement_area_m2: Optional[float] = None
    optical_only_area_m2: Optional[float] = None
    sar_only_area_m2: Optional[float] = None
    total_detected_area_m2: Optional[float] = None

    # Fused confidence
    mean_fused_confidence: float = 0.0
    consensus_confidence_gain: float = 0.0  # Boost from multi-sensor agreement

    # Binary and categorical spatial masks
    agreement_mask: Optional[np.ndarray] = None  # (H, W) bool: both agree
    optical_only_mask: Optional[np.ndarray] = None
    sar_only_mask: Optional[np.ndarray] = None
    fused_confidence_map: Optional[np.ndarray] = None  # (H, W) float32 [0.0, 1.0]

    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_masks: bool = False) -> Dict[str, Any]:
        res = {
            "task_name": self.task_name,
            "total_pixels": self.total_analyzed_pixels,
            "metrics": {
                "iou": round(self.iou, 4),
                "dice": round(self.dice_coefficient, 4),
                "agreement_ratio": round(self.spatial_agreement_ratio, 4),
                "cohens_kappa": round(self.cohens_kappa, 4),
                "fused_confidence": round(self.mean_fused_confidence, 3),
                "consensus_confidence_gain": round(self.consensus_confidence_gain, 3),
            },
            "pixel_counts": {
                "agreement": self.agreement_pixels,
                "optical_only": self.optical_only_pixels,
                "sar_only": self.sar_only_pixels,
                "neither": self.neither_pixels,
            },
            "areas_m2": {
                "agreement": self.agreement_area_m2,
                "optical_only": self.optical_only_area_m2,
                "sar_only": self.sar_only_area_m2,
                "total_union": self.total_detected_area_m2,
            },
            "diagnostics": self.diagnostics,
        }
        if include_masks and self.agreement_mask is not None:
            res["mask_shape"] = list(self.agreement_mask.shape)
        return res


class SpatialFusionEngine:
    """Engine for fusing pixel-level detections between optical and SAR sensors."""

    def fuse_binary_detections(
        self,
        optical_mask: np.ndarray,
        sar_mask: np.ndarray,
        task_name: str = "water_body_detection",
        optical_confidence: Optional[np.ndarray] = None,
        sar_confidence: Optional[np.ndarray] = None,
        pixel_size_meters: Optional[float] = None,
    ) -> FusionResult:
        """Fuse two binary masks from optical and SAR sensors.
        
        Args:
            optical_mask: (H, W) boolean or 0/1 array.
            sar_mask: (H, W) boolean or 0/1 array.
            task_name: Description of target feature.
            optical_confidence: Optional (H, W) float array in [0, 1].
            sar_confidence: Optional (H, W) float array in [0, 1].
            pixel_size_meters: Ground resolution (e.g. 10.0 for Sentinel).
            
        Returns:
            FusionResult with full spatial metrics and confidence map.
        """
        opt_b = (optical_mask > 0).astype(bool)
        sar_b = (sar_mask > 0).astype(bool)

        if opt_b.shape != sar_b.shape:
            raise ValueError(
                f"Shape mismatch in fusion: Optical {opt_b.shape} vs SAR {sar_b.shape}. "
                "Co-registration must be applied before fusion."
            )

        total_pixels = int(opt_b.size)

        # 1. Spatial logic operations
        agreement = opt_b & sar_b
        optical_only = opt_b & (~sar_b)
        sar_only = (~opt_b) & sar_b
        neither = (~opt_b) & (~sar_b)

        n_agree = int(np.sum(agreement))
        n_opt_only = int(np.sum(optical_only))
        n_sar_only = int(np.sum(sar_only))
        n_neither = int(np.sum(neither))
        n_union = n_agree + n_opt_only + n_sar_only

        # 2. Overlap metrics
        iou = float(n_agree / max(1, n_union))
        dice = float((2.0 * n_agree) / max(1, (2 * n_agree + n_opt_only + n_sar_only)))
        agreement_ratio = float(n_agree / max(1, n_union))

        # Cohen's Kappa calculation
        # Po = observed accuracy
        po = (n_agree + n_neither) / max(1, total_pixels)
        # Pe = expected accuracy by chance
        p_opt_pos = (n_agree + n_opt_only) / max(1, total_pixels)
        p_opt_neg = 1.0 - p_opt_pos
        p_sar_pos = (n_agree + n_sar_only) / max(1, total_pixels)
        p_sar_neg = 1.0 - p_sar_pos
        pe = (p_opt_pos * p_sar_pos) + (p_opt_neg * p_sar_neg)
        kappa = float((po - pe) / max(1e-6, 1.0 - pe)) if (1.0 - pe) > 1e-6 else 1.0
        kappa = max(-1.0, min(1.0, kappa))

        # 3. Physical area conversions
        area_m2_factor = (pixel_size_meters ** 2) if pixel_size_meters else None
        agree_m2 = round(n_agree * area_m2_factor, 2) if area_m2_factor else None
        opt_m2 = round(n_opt_only * area_m2_factor, 2) if area_m2_factor else None
        sar_m2 = round(n_sar_only * area_m2_factor, 2) if area_m2_factor else None
        union_m2 = round(n_union * area_m2_factor, 2) if area_m2_factor else None

        # 4. Spatially resolved confidence modeling
        # Agreement gets a multi-sensor consensus boost (+15%)
        # Disagreement is bounded by the single reporting sensor's reliability
        fused_conf_map = np.full(opt_b.shape, 0.50, dtype=np.float32)

        # Baseline per-pixel sensor confidence
        opt_conf = optical_confidence if optical_confidence is not None else np.full(opt_b.shape, 0.80, dtype=np.float32)
        sar_conf = sar_confidence if sar_confidence is not None else np.full(sar_b.shape, 0.82, dtype=np.float32)

        # Dual-sensor consensus: 1 - (1 - P1)*(1 - P2)
        consensus_prob = 1.0 - (1.0 - opt_conf) * (1.0 - sar_conf)
        fused_conf_map[agreement] = np.clip(consensus_prob[agreement] * 1.05, 0.85, 0.99)

        # Single sensor detections have lower confidence due to lack of corroboration
        fused_conf_map[optical_only] = np.clip(opt_conf[optical_only] * 0.80, 0.40, 0.75)
        fused_conf_map[sar_only] = np.clip(sar_conf[sar_only] * 0.85, 0.45, 0.80)
        fused_conf_map[neither] = 0.95  # High confidence that neither detected phenomenon

        mean_fused_conf = float(np.mean(fused_conf_map[opt_b | sar_b])) if n_union > 0 else 0.90
        consensus_gain = float(np.mean(fused_conf_map[agreement]) - np.mean(opt_conf[opt_b])) if n_agree > 0 and np.any(opt_b) else 0.0

        diagnostics = {
            "optical_positive_pixels": n_agree + n_opt_only,
            "sar_positive_pixels": n_agree + n_sar_only,
            "consensus_percentage_of_union": round((n_agree / max(1, n_union)) * 100.0, 1),
            "disagreement_percentage_of_union": round(((n_opt_only + n_sar_only) / max(1, n_union)) * 100.0, 1),
        }

        return FusionResult(
            task_name=task_name,
            total_analyzed_pixels=total_pixels,
            pixel_size_meters=pixel_size_meters,
            agreement_pixels=n_agree,
            optical_only_pixels=n_opt_only,
            sar_only_pixels=n_sar_only,
            neither_pixels=n_neither,
            iou=round(iou, 4),
            dice_coefficient=round(dice, 4),
            spatial_agreement_ratio=round(agreement_ratio, 4),
            cohens_kappa=round(kappa, 4),
            agreement_area_m2=agree_m2,
            optical_only_area_m2=opt_m2,
            sar_only_area_m2=sar_m2,
            total_detected_area_m2=union_m2,
            mean_fused_confidence=round(mean_fused_conf, 3),
            consensus_confidence_gain=round(consensus_gain, 3),
            agreement_mask=agreement,
            optical_only_mask=optical_only,
            sar_only_mask=sar_only,
            fused_confidence_map=fused_conf_map,
            diagnostics=diagnostics,
        )
