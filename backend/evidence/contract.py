"""
Canonical EvidenceContract + EvidenceGate.

Per audit sections 27-29: every analytical output must carry real
provenance (no default confidence values), and every result must pass
through a single gate that decides ANSWER / QUALIFY / ABSTAIN. Map, chat,
evidence panel, and report must all render from the *same* object this
module produces — never a per-surface recomputation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EvidenceStrength(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"


class Decision(str, Enum):
    ANSWER = "ANSWER"
    QUALIFY = "QUALIFY"
    ABSTAIN = "ABSTAIN"


class EvidenceContractError(ValueError):
    pass


@dataclass
class ProvenanceStep:
    step: int
    tool: str
    duration_ms: float
    inputs_hash: Optional[str] = None
    outputs_hash: Optional[str] = None


@dataclass
class EvidenceFactors:
    """
    Named, inspectable contributing factors — never collapsed into a
    single opaque "confidence: 0.94". Each factor is either a real
    measured value or explicitly None (meaning: not evaluated / not
    applicable), never a silent default.
    """
    model_confidence: Optional[float] = None          # from a VERIFIED model only
    registration_quality: Optional[float] = None       # e.g. 1 - normalized RMSE
    gsd_resolution_rating: Optional[float] = None
    cloud_contamination: Optional[float] = None         # fraction, lower is better
    cross_modal_agreement: Optional[float] = None       # optical vs SAR agreement
    band_availability: Optional[float] = None            # fraction of required bands present
    data_provenance_complete: Optional[bool] = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class EvidenceContract:
    id: str
    task: str
    model_ids: list[str]                       # from ModelRegistry, must all be READY or explicitly ABSENT
    is_real_weights: bool
    fallback_used: bool
    observation_ids: list[str]                  # ObservationRecord.observation_id, never inline metadata
    claim: str
    spatial_evidence: Optional[dict[str, Any]]   # real GeoJSON FeatureCollection, or None
    metrics: dict[str, Any]
    factors: EvidenceFactors
    provenance_steps: list[ProvenanceStep] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.fallback_used and self.is_real_weights:
            raise EvidenceContractError(
                "is_real_weights cannot be True while fallback_used is True — "
                "these are contradictory. A fallback path is by definition "
                "not the real model."
            )
        if not self.observation_ids:
            raise EvidenceContractError(
                "EvidenceContract requires at least one real observation_id; "
                "results not traceable to a real observation cannot be issued."
            )


def compute_evidence_strength(factors: EvidenceFactors) -> EvidenceStrength:
    """
    Deterministic, inspectable strength grading — replaces the flagged
    'Platt-Calibrated 94%' pattern. Every branch below is explainable in
    one sentence; there is no learned/opaque scoring step here.
    """
    values = [v for v in (
        factors.model_confidence,
        factors.registration_quality,
        factors.gsd_resolution_rating,
        factors.cross_modal_agreement,
        factors.band_availability,
    ) if v is not None]

    if not values:
        return EvidenceStrength.INSUFFICIENT

    worst = min(values)
    avg = sum(values) / len(values)

    if factors.cloud_contamination is not None and factors.cloud_contamination > 0.6:
        return EvidenceStrength.LIMITED

    if worst < 0.3:
        return EvidenceStrength.INSUFFICIENT
    if worst < 0.55 or avg < 0.6:
        return EvidenceStrength.LIMITED
    if worst < 0.75 or avg < 0.8:
        return EvidenceStrength.MODERATE
    return EvidenceStrength.STRONG


@dataclass
class GateResult:
    decision: Decision
    strength: EvidenceStrength
    reasons: list[str]
    contract: EvidenceContract


def evidence_gate(
    contract: EvidenceContract,
    *,
    has_spatial_evidence_required: bool = True,
) -> GateResult:
    """
    The single mandatory decision point. Nothing downstream (map/chat/
    report) should render a "finding" that didn't come through here.
    """
    reasons: list[str] = []
    strength = compute_evidence_strength(contract.factors)

    if contract.fallback_used:
        reasons.append(
            "Fallback path was used (not the primary model); result cannot "
            "be presented as full-confidence model output."
        )

    if has_spatial_evidence_required and not contract.spatial_evidence:
        reasons.append("No spatial evidence (empty geometry) was produced.")

    if strength == EvidenceStrength.INSUFFICIENT:
        return GateResult(
            decision=Decision.ABSTAIN,
            strength=strength,
            reasons=reasons + ["Evidence strength graded INSUFFICIENT."],
            contract=contract,
        )

    if reasons or strength == EvidenceStrength.LIMITED:
        return GateResult(
            decision=Decision.QUALIFY,
            strength=strength,
            reasons=reasons or ["Evidence strength graded LIMITED."],
            contract=contract,
        )

    return GateResult(decision=Decision.ANSWER, strength=strength, reasons=[], contract=contract)
