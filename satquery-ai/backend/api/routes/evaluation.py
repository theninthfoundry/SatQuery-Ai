"""Benchmark evaluation routes."""

from fastapi import APIRouter
from ...evaluation import benchmark_harness

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


@router.get("/benchmarks")
def list_benchmarks():
    """List available benchmark evaluation datasets."""
    return {
        "available_benchmarks": [
            {
                "id": "rsvqa_hr",
                "name": "RSVQA-HR / VRSBench",
                "task": "Single-Image Visual Question Answering",
                "metric": "Accuracy (%) / BLEU-4",
            },
            {
                "id": "rs_grounding",
                "name": "RS Visual Grounding (GeoChat / GeoPixel)",
                "task": "Referring Expression Grounding",
                "metric": "Mean IoU (%) / Precision @ 0.5",
            },
            {
                "id": "cdvqa",
                "name": "CDVQA / Siamese ChangeNet",
                "task": "Bi-Temporal Change Detection & QA",
                "metric": "Change F1 (%) / Mask IoU",
            },
            {
                "id": "bigearthnet",
                "name": "BigEarthNet.txt",
                "task": "Optical + SAR Multimodal Corroboration",
                "metric": "Cross-Modal Agreement (%) / Macro F1",
            },
        ]
    }


@router.post("/run")
def run_evaluation_suite():
    """Execute the multi-task remote sensing benchmark evaluation suite."""
    result = benchmark_harness.run_all()
    return result
