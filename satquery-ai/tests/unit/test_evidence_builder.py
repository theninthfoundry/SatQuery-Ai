"""Unit tests for Evidence Builder and Confidence calculation."""

from backend.evidence.confidence import (
    compute_vqa_confidence,
    calculate_spatial_resolution_score,
    compute_multimodal_confidence,
)
from backend.evidence.builder import build_evidence
from backend.evidence.provenance import ExecutionStep


def test_confidence_calculation_vqa():
    # 10m Sentinel-2 GSD with 0.90 model confidence
    conf = compute_vqa_confidence(model_confidence=0.90, x_res=10.0, y_res=10.0)
    assert 0.0 <= conf.overall <= 1.0
    assert conf.model_score == 0.90
    assert conf.resolution_score == 0.90
    assert len(conf.notes) >= 2


def test_confidence_calculation_multimodal():
    conf = compute_multimodal_confidence(
        model_confidence=0.85,
        registration_quality=0.95,
        sar_agreement=0.80,
        x_res=10.0,
        y_res=10.0,
    )
    assert 0.80 <= conf.overall <= 0.95
    assert conf.sar_agreement_score == 0.80


def test_build_evidence():
    conf = compute_vqa_confidence(model_confidence=0.90, x_res=10.0, y_res=10.0)
    steps = [
        ExecutionStep(
            step_number=1,
            tool="vqa_inference",
            description="Ran VQA",
            status="completed",
            duration_ms=120,
        )
    ]
    evi = build_evidence(
        claim="Water body present in north-east quadrant",
        source_analysis_id="job_123",
        source_image_ids=["img_abc"],
        model_used="geochat_7b",
        confidence=conf,
        execution_steps=steps,
    )

    assert evi.id.startswith("evi_")
    assert evi.claim == "Water body present in north-east quadrant"
    assert len(evi.execution_steps) == 1
    assert evi.confidence.overall > 0.0
