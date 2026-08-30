"""Standardized Evidence Contract for SatQuery AI.

Guarantees that all specialist models, pipelines, and deterministic geospatial tools
produce a uniform, verifiable, and auditable evidence structure.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProvenanceStep:
    step_number: int
    tool: str
    description: str
    status: str
    duration_ms: int
    model: Optional[str] = None
    output_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "tool": self.tool,
            "description": self.description,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "output_summary": self.output_summary,
        }


@dataclass
class EvidenceContract:
    """Canonical Evidence Contract produced by every perception and measurement tool."""
    id: str
    task: str
    model: str
    is_real_weights: bool
    fallback_used: bool
    inputs: List[str]
    claim: str
    prediction_summary: str
    spatial_evidence: Optional[Dict[str, Any]] = None  # GeoJSON FeatureCollection
    metrics: Dict[str, Any] = field(default_factory=dict)
    reliability_score: float = 0.0                     # Evidence Reliability Index (0.0 - 1.0)
    reliability_factors: Dict[str, float] = field(default_factory=dict)
    provenance_steps: List[ProvenanceStep] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "model": self.model,
            "is_real_weights": self.is_real_weights,
            "fallback_used": self.fallback_used,
            "inputs": self.inputs,
            "claim": self.claim,
            "prediction_summary": self.prediction_summary,
            "spatial_evidence": self.spatial_evidence,
            "metrics": self.metrics,
            "reliability_score": self.reliability_score,
            "reliability_factors": self.reliability_factors,
            "provenance_steps": [s.to_dict() for s in self.provenance_steps],
            "artifacts": self.artifacts,
            "limitations": self.limitations,
            "created_at": self.created_at,
        }


def create_evidence_contract(
    task: str,
    model: str,
    inputs: List[str],
    claim: str,
    prediction_summary: str,
    is_real_weights: bool,
    fallback_used: bool,
    spatial_evidence: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    reliability_score: float = 0.85,
    reliability_factors: Optional[Dict[str, float]] = None,
    provenance_steps: Optional[List[ProvenanceStep]] = None,
    artifacts: Optional[List[str]] = None,
    limitations: Optional[List[str]] = None,
) -> EvidenceContract:
    """Factory function for creating standardized Evidence Contracts."""
    return EvidenceContract(
        id=f"evi_{uuid.uuid4().hex[:10]}",
        task=task,
        model=model,
        is_real_weights=is_real_weights,
        fallback_used=fallback_used,
        inputs=inputs,
        claim=claim,
        prediction_summary=prediction_summary,
        spatial_evidence=spatial_evidence,
        metrics=metrics or {},
        reliability_score=round(reliability_score, 2),
        reliability_factors=reliability_factors or {"model_score": 0.70, "resolution_score": 0.30},
        provenance_steps=provenance_steps or [],
        artifacts=artifacts or [],
        limitations=limitations or ["Analysis bounded by sensor Ground Sampling Distance (GSD)."],
    )
