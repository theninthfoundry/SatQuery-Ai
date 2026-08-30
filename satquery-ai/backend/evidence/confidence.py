"""Deterministic confidence calculation engine for SatQuery AI.

Adheres strictly to the architectural principle:
Confidence is computed from measurable signals (model logits, spatial resolution / GSD,
and registration quality), never fabricated or hallucinated by an LLM.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ConfidenceScore:
    overall: float
    model_score: float
    resolution_score: float
    registration_score: Optional[float] = None
    sar_agreement_score: Optional[float] = None
    factors: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "model_score": self.model_score,
            "resolution_score": self.resolution_score,
            "registration_score": self.registration_score,
            "sar_agreement_score": self.sar_agreement_score,
            "factors": self.factors,
            "notes": self.notes,
        }


def calculate_spatial_resolution_score(x_res: float, y_res: float, task_type: str = "vqa") -> float:
    """Evaluate whether the spatial resolution (GSD) is adequate for the requested task.
    
    - Very high resolution (<1m): score = 1.0
    - High resolution (1m - 10m Sentinel-2): score = 0.85 - 0.95
    - Moderate resolution (10m - 30m Landsat): score = 0.70 - 0.85
    - Coarse resolution (>30m): score = 0.50
    """
    avg_res = (abs(x_res) + abs(y_res)) / 2.0
    if avg_res <= 1.0:
        return 1.0
    elif avg_res <= 5.0:
        return 0.95
    elif avg_res <= 10.0:
        return 0.90
    elif avg_res <= 30.0:
        return 0.75
    else:
        return 0.55


def compute_vqa_confidence(
    model_confidence: float,
    x_res: float = 10.0,
    y_res: float = 10.0,
    box_area_ratio: Optional[float] = None,
) -> ConfidenceScore:
    """Compute verified confidence for a single-image VQA or Grounding task."""
    res_score = calculate_spatial_resolution_score(x_res, y_res, task_type="vqa")

    # Weights: 70% model confidence from softmax/logits, 30% spatial GSD suitability
    weights = {"model": 0.70, "resolution": 0.30}
    overall = (model_confidence * weights["model"]) + (res_score * weights["resolution"])
    overall = round(max(0.0, min(1.0, overall)), 2)

    notes = [
        f"Model certainty: {int(model_confidence * 100)}%",
        f"Spatial resolution rating: {int(res_score * 100)}% (GSD: {round(x_res, 1)}m)",
    ]

    if box_area_ratio is not None and box_area_ratio < 0.001:
        notes.append("Warning: Grounded object is extremely small relative to scene dimensions.")

    return ConfidenceScore(
        overall=overall,
        model_score=round(model_confidence, 2),
        resolution_score=round(res_score, 2),
        factors=weights,
        notes=notes,
    )


def compute_multimodal_confidence(
    model_confidence: float,
    registration_quality: float,
    sar_agreement: Optional[float] = None,
    x_res: float = 10.0,
    y_res: float = 10.0,
) -> ConfidenceScore:
    """Compute confidence for bi-temporal or optical-SAR analysis."""
    res_score = calculate_spatial_resolution_score(x_res, y_res)

    if sar_agreement is not None:
        weights = {"model": 0.45, "registration": 0.30, "sar": 0.15, "resolution": 0.10}
        overall = (
            (model_confidence * weights["model"])
            + (registration_quality * weights["registration"])
            + (sar_agreement * weights["sar"])
            + (res_score * weights["resolution"])
        )
    else:
        weights = {"model": 0.55, "registration": 0.30, "resolution": 0.15}
        overall = (
            (model_confidence * weights["model"])
            + (registration_quality * weights["registration"])
            + (res_score * weights["resolution"])
        )

    overall = round(max(0.0, min(1.0, overall)), 2)

    notes = [
        f"Model probability: {int(model_confidence * 100)}%",
        f"Co-registration quality: {int(registration_quality * 100)}%",
    ]
    if sar_agreement is not None:
        notes.append(f"SAR cross-modal agreement: {int(sar_agreement * 100)}%")

    return ConfidenceScore(
        overall=overall,
        model_score=round(model_confidence, 2),
        resolution_score=round(res_score, 2),
        registration_score=round(registration_quality, 2),
        sar_agreement_score=round(sar_agreement, 2) if sar_agreement is not None else None,
        factors=weights,
        notes=notes,
    )
