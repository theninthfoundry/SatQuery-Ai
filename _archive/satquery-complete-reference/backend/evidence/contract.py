"""
backend/evidence/contract.py

The single canonical output type every specialist pipeline must return.
Nothing leaves the agent without being wrapped in an EvidenceContract --
this is what makes the system auditable rather than a black box.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


def new_evidence_id() -> str:
    return f"evi_{uuid.uuid4().hex[:10]}"


@dataclass
class ProvenanceStep:
    step: int
    tool: str
    duration_ms: float
    detail: Optional[str] = None


@dataclass
class ReliabilityFactors:
    model_confidence: float          # raw model output confidence / softmax
    registration_quality: float      # spatial pair overlap / CRS agreement
    gsd_resolution_rating: float     # 0-1, penalizes coarse GSD
    fallback_penalty: float = 0.0    # subtracted when a heuristic fallback was used


@dataclass
class EvidenceContract:
    id: str
    task: str
    model: str
    is_real_weights: bool
    fallback_used: bool
    inputs: list
    claim: str
    spatial_evidence: Optional[dict]   # GeoJSON FeatureCollection or None
    metrics: dict
    reliability_score: float
    reliability_factors: dict
    provenance_steps: list
    created_at_unix: float = field(default_factory=time.time)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ProvenanceTracer:
    """Attach to a pipeline run; every tool call records its own timing.
    Keeps timing honest -- callers pass real elapsed time, this class
    doesn't invent numbers."""

    def __init__(self):
        self._steps: list[ProvenanceStep] = []
        self._counter = 0

    def record(self, tool: str, duration_ms: float, detail: Optional[str] = None):
        self._counter += 1
        self._steps.append(ProvenanceStep(self._counter, tool, round(duration_ms, 2), detail))

    def timed(self, tool: str):
        """Context manager: `with tracer.timed('affine_transform'): ...`"""
        return _TimedStep(self, tool)

    @property
    def steps(self) -> list:
        return [asdict(s) for s in self._steps]


class _TimedStep:
    def __init__(self, tracer: ProvenanceTracer, tool: str):
        self.tracer = tracer
        self.tool = tool
        self._t0 = None

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        dur_ms = (time.perf_counter() - self._t0) * 1000.0
        detail = f"error: {exc}" if exc else None
        self.tracer.record(self.tool, dur_ms, detail)
        return False  # never swallow exceptions


def compute_reliability(model_confidence: float, registration_quality: float,
                         gsd_resolution_rating: float, fallback_used: bool,
                         fallback_penalty: float = 0.15) -> tuple:
    """
    GSD-weighted reliability score, README-consistent: a weighted blend
    of (a) the specialist model's own confidence, (b) how well-registered
    the input pair was (1.0 for single image), and (c) resolution
    adequacy for the requested task, minus a penalty if a classical-CV
    fallback stood in for a neural model.
    """
    weights = {"model_confidence": 0.5, "registration_quality": 0.25, "gsd": 0.25}
    raw = (
        weights["model_confidence"] * model_confidence
        + weights["registration_quality"] * registration_quality
        + weights["gsd"] * gsd_resolution_rating
    )
    penalty = fallback_penalty if fallback_used else 0.0
    score = max(0.0, min(1.0, raw - penalty))
    factors = ReliabilityFactors(
        model_confidence=round(model_confidence, 4),
        registration_quality=round(registration_quality, 4),
        gsd_resolution_rating=round(gsd_resolution_rating, 4),
        fallback_penalty=penalty,
    )
    return round(score, 4), asdict(factors)


def gsd_rating(gsd_m_per_px: float, task: str) -> float:
    """Heuristic resolution-adequacy curve per task. Change detection and
    grounding need finer GSD than a broad VQA scene description."""
    thresholds = {
        "vqa": (30.0, 100.0),
        "captioning": (30.0, 100.0),
        "grounding": (5.0, 30.0),
        "change_detection": (5.0, 30.0),
        "fusion": (10.0, 40.0),
    }
    good, bad = thresholds.get(task, (10.0, 50.0))
    if gsd_m_per_px <= good:
        return 1.0
    if gsd_m_per_px >= bad:
        return 0.3
    frac = (bad - gsd_m_per_px) / (bad - good)
    return round(0.3 + 0.7 * frac, 4)


def build_evidence(task: str, model: str, is_real_weights: bool, fallback_used: bool,
                    inputs: list, claim: str, spatial_evidence: Optional[dict],
                    metrics: dict, reliability_score: float, reliability_factors: dict,
                    tracer: ProvenanceTracer, warnings: Optional[list] = None) -> EvidenceContract:
    return EvidenceContract(
        id=new_evidence_id(),
        task=task,
        model=model,
        is_real_weights=is_real_weights,
        fallback_used=fallback_used,
        inputs=inputs,
        claim=claim,
        spatial_evidence=spatial_evidence,
        metrics=metrics,
        reliability_score=reliability_score,
        reliability_factors=reliability_factors,
        provenance_steps=tracer.steps,
        warnings=warnings or [],
    )
