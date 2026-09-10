"""Canonical Evidence Builder for SatQuery AI."""

import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .confidence import ConfidenceScore
from .provenance import ExecutionStep, ProvenanceGraph


@dataclass
class EvidenceObject:
    id: str
    claim: str
    source_analysis_id: str
    source_image_ids: List[str]
    model_used: str
    output_geometry: Optional[Dict[str, Any]]
    confidence: ConfidenceScore
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "source_analysis_id": self.source_analysis_id,
            "source_image_ids": self.source_image_ids,
            "model_used": self.model_used,
            "output_geometry": self.output_geometry,
            "confidence": self.confidence.to_dict(),
            "execution_steps": [s.to_dict() for s in self.execution_steps],
            "artifacts": self.artifacts,
            "created_at": self.created_at,
        }


def build_evidence(
    claim: str,
    source_analysis_id: str,
    source_image_ids: List[str],
    model_used: str,
    confidence: ConfidenceScore,
    output_geometry: Optional[Dict[str, Any]] = None,
    execution_steps: Optional[List[ExecutionStep]] = None,
    artifacts: Optional[List[str]] = None,
) -> EvidenceObject:
    """Build and validate a verifiable EvidenceObject."""
    evidence_id = f"evi_{uuid.uuid4().hex[:10]}"
    return EvidenceObject(
        id=evidence_id,
        claim=claim,
        source_analysis_id=source_analysis_id,
        source_image_ids=source_image_ids,
        model_used=model_used,
        output_geometry=output_geometry,
        confidence=confidence,
        execution_steps=execution_steps or [],
        artifacts=artifacts or [],
    )
