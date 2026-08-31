"""Evidence and provenance package."""

from .confidence import (
    ConfidenceScore,
    compute_vqa_confidence,
    compute_multimodal_confidence,
    calculate_spatial_resolution_score,
)
from .calibration import (
    platt_scale,
    fit_platt_scaling,
    compute_calibration_metrics,
    CalibrationReport,
    ReliabilityBin,
)
from .provenance import ExecutionStep, ProvenanceGraph
from .builder import build_evidence, EvidenceObject
from .contract import (
    EvidenceContract,
    ProvenanceStep,
    create_evidence_contract,
)

__all__ = [
    "ConfidenceScore",
    "compute_vqa_confidence",
    "compute_multimodal_confidence",
    "calculate_spatial_resolution_score",
    "platt_scale",
    "fit_platt_scaling",
    "compute_calibration_metrics",
    "CalibrationReport",
    "ReliabilityBin",
    "ExecutionStep",
    "ProvenanceGraph",
    "build_evidence",
    "EvidenceObject",
    "EvidenceContract",
    "ProvenanceStep",
    "create_evidence_contract",
]
