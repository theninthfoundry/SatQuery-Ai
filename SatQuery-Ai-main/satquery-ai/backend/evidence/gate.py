"""Evidence Gate for Scientific Refusal and Calibrated Answering.

Enforces epistemological rigor:
1. ANSWER: Sufficient, high-quality corroborating evidence.
2. QUALIFY: Answer provided with mandatory scientific caveats.
3. ABSTAIN: Explicit scientific refusal when evidence is invalid, contaminated, or missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from .graph import EvidenceGraph


class GateDecision(str, Enum):
    """The epistemological stance taken on a query."""
    ANSWER = "answer"      # High confidence, sufficient evidence
    QUALIFY = "qualify"    # Answer provided, but caveats required
    ABSTAIN = "abstain"    # Refuse to answer on scientific grounds


@dataclass
class GateResult:
    """Decision output from the Evidence Gate."""
    decision: GateDecision
    confidence: float
    reasons: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "caveats": self.caveats,
            "recommended_action": self.recommended_action,
        }


class EvidenceGate:
    """Gating engine that prevents hallucinated or scientifically unsound conclusions."""

    # Absolute refusal thresholds
    MIN_REGISTRATION_SCORE: float = 0.50
    MIN_SPATIAL_OVERLAP: float = 0.10
    MAX_CLOUD_CONTAMINATION: float = 0.65
    MIN_CONFIDENCE_THRESHOLD: float = 0.45

    def evaluate(
        self,
        claim_description: str,
        evidence_graph: Optional[EvidenceGraph] = None,
        registration_quality: float = 1.0,
        spatial_overlap: float = 1.0,
        cloud_fraction: float = 0.0,
        model_confidence: Optional[float] = None,
        has_cross_modal_corroboration: bool = False,
    ) -> GateResult:
        """Evaluate evidence quality and decide whether to ANSWER, QUALIFY, or ABSTAIN."""
        reasons: List[str] = []
        caveats: List[str] = []

        # 1. Hard Scientific Abstention Conditions
        if registration_quality < self.MIN_REGISTRATION_SCORE:
            reasons.append(
                f"Image co-registration score ({registration_quality:.2f}) is below the minimum threshold ({self.MIN_REGISTRATION_SCORE}). "
                "Images cannot be reliably aligned without spatial hallucination."
            )
            return GateResult(
                decision=GateDecision.ABSTAIN,
                confidence=registration_quality,
                reasons=reasons,
                recommended_action="Re-run image co-registration with AKAZE or verify georeferencing metadata.",
            )

        if spatial_overlap < self.MIN_SPATIAL_OVERLAP:
            reasons.append(
                f"Spatial overlap between observations ({spatial_overlap * 100:.1f}%) is insufficient for comparison."
            )
            return GateResult(
                decision=GateDecision.ABSTAIN,
                confidence=spatial_overlap,
                reasons=reasons,
                recommended_action="Ensure both temporal or multimodal observations cover the same Area of Interest (AOI).",
            )

        if cloud_fraction > self.MAX_CLOUD_CONTAMINATION and not has_cross_modal_corroboration:
            reasons.append(
                f"Cloud contamination ({cloud_fraction * 100:.1f}%) exceeds acceptable operational threshold ({self.MAX_CLOUD_CONTAMINATION * 100:.0f}%) "
                "and no SAR microwave radar asset was provided to penetrate cloud cover."
            )
            return GateResult(
                decision=GateDecision.ABSTAIN,
                confidence=0.30,
                reasons=reasons,
                recommended_action="Upload a corresponding Sentinel-1 or RISAT SAR observation to penetrate cloud cover.",
            )

        # 2. Qualification Checks (Answer with Warning)
        base_conf = model_confidence if model_confidence is not None else round(registration_quality * (1.0 - cloud_fraction * 0.4), 3)
        effective_conf = base_conf

        if 0.30 <= cloud_fraction <= self.MAX_CLOUD_CONTAMINATION:
            caveats.append(
                f"Optical observations contain {cloud_fraction * 100:.1f}% cloud/haze. "
                "Spectral indices in obscured pixels may exhibit degraded reliability."
            )
            effective_conf *= 0.85

        if registration_quality < 0.70:
            caveats.append(
                f"Co-registration accuracy is moderate ({registration_quality:.2f}). "
                "Perimeter boundary changes should be interpreted with caution."
            )
            effective_conf *= 0.90

        if not has_cross_modal_corroboration and model_confidence is not None and model_confidence < 0.75:
            caveats.append(
                "Finding is based on single-sensor optical inference without SAR cross-verification."
            )
            effective_conf *= 0.92

        if caveats:
            return GateResult(
                decision=GateDecision.QUALIFY,
                confidence=round(effective_conf, 3),
                reasons=["Evidence is present but subject to environmental or sensor caveats."],
                caveats=caveats,
            )

        # 3. Clean Scientific Answer
        return GateResult(
            decision=GateDecision.ANSWER,
            confidence=round(effective_conf, 3),
            reasons=["All scientific validation criteria met with robust evidence grounding."],
            caveats=[],
        )
