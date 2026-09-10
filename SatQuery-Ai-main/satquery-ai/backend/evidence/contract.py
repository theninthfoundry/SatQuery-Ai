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
    execution_mode: str = "real_execution"  # real_execution, trained_model, untrained_model, classical_fallback, demo, partial, failed
    checkpoint: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    acquisition_metadata: Dict[str, Any] = field(default_factory=dict)
    sensor_metadata: Dict[str, Any] = field(default_factory=dict)
    prediction: Optional[Dict[str, Any]] = None
    spatial_evidence: Optional[Dict[str, Any]] = None  # GeoJSON FeatureCollection
    metrics: Dict[str, Any] = field(default_factory=dict)
    reliability_score: float = 0.0                     # Evidence Reliability Index (0.0 - 1.0)
    reliability_factors: Dict[str, float] = field(default_factory=dict)
    provenance_steps: List[ProvenanceStep] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "execution_mode": self.execution_mode,
            "model": self.model,
            "checkpoint": self.checkpoint,
            "checkpoint_sha256": self.checkpoint_sha256,
            "is_real_weights": self.is_real_weights,
            "fallback_used": self.fallback_used,
            "inputs": self.inputs,
            "acquisition_metadata": self.acquisition_metadata,
            "sensor_metadata": self.sensor_metadata,
            "claim": self.claim,
            "prediction": self.prediction,
            "prediction_summary": self.prediction_summary,
            "spatial_evidence": self.spatial_evidence,
            "metrics": self.metrics,
            "reliability_score": self.reliability_score,
            "reliability_factors": self.reliability_factors,
            "provenance_steps": [s.to_dict() for s in self.provenance_steps],
            "artifacts": self.artifacts,
            "limitations": self.limitations,
            "warnings": self.warnings,
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
    execution_mode: str = "real_execution",
    checkpoint: Optional[str] = None,
    checkpoint_sha256: Optional[str] = None,
    acquisition_metadata: Optional[Dict[str, Any]] = None,
    sensor_metadata: Optional[Dict[str, Any]] = None,
    prediction: Optional[Dict[str, Any]] = None,
    spatial_evidence: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    reliability_score: float = 0.0,
    reliability_factors: Optional[Dict[str, float]] = None,
    provenance_steps: Optional[List[ProvenanceStep]] = None,
    artifacts: Optional[List[str]] = None,
    limitations: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> EvidenceContract:
    """Factory function for creating standardized Evidence Contracts."""
    if not is_real_weights and fallback_used and execution_mode == "real_execution":
        execution_mode = "classical_fallback"

    return EvidenceContract(
        id=f"evi_{uuid.uuid4().hex[:10]}",
        task=task,
        model=model,
        is_real_weights=is_real_weights,
        fallback_used=fallback_used,
        execution_mode=execution_mode,
        checkpoint=checkpoint,
        checkpoint_sha256=checkpoint_sha256,
        inputs=inputs,
        acquisition_metadata=acquisition_metadata or {},
        sensor_metadata=sensor_metadata or {},
        claim=claim,
        prediction=prediction,
        prediction_summary=prediction_summary,
        spatial_evidence=spatial_evidence,
        metrics=metrics or {},
        reliability_score=round(reliability_score, 3),
        reliability_factors=reliability_factors or {},
        provenance_steps=provenance_steps or [],
        artifacts=artifacts or [],
        limitations=limitations or ["Spatial resolution and pixel bounds conform to sensor specifications."],
        warnings=warnings or [],
    )
