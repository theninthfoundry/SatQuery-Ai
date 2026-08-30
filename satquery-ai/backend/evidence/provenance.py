"""Provenance graph and execution trace structures for auditable AI reasoning."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionStep:
    step_number: int
    tool: str
    description: str
    status: str  # "completed", "failed", "skipped"
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
class ProvenanceGraph:
    analysis_id: str
    source_images: List[str]
    model_runs: List[Dict[str, Any]]
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "source_images": self.source_images,
            "model_runs": self.model_runs,
            "execution_steps": [s.to_dict() for s in self.execution_steps],
            "created_at": self.created_at,
        }
