"""Single-image remote-sensing VQA perception pipeline."""

import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models_db import ImageRecord, AnalysisJob
from ..models.geochat import geochat_adapter
from ..evidence import (
    build_evidence,
    compute_vqa_confidence,
    ExecutionStep,
    EvidenceObject,
)


def run_single_image_vqa_pipeline(
    image_id: str,
    question: str,
    db: Session,
) -> Dict[str, Any]:
    """Execute the end-to-end Single-Image VQA pipeline with auditable evidence generation."""
    steps = []
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    start_total_t = time.perf_counter()

    # Step 1: Image retrieval & validation
    t0 = time.perf_counter()
    image_row = db.get(ImageRecord, image_id)
    if not image_row:
        raise ValueError(f"Image '{image_id}' not found in database.")

    image_path = Path(image_row.path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image raster not found on disk at {image_path}")

    steps.append(
        ExecutionStep(
            step_number=1,
            tool="retrieve_image_asset",
            description=f"Loaded raster {image_row.filename} ({image_row.width}x{image_row.height}, {image_row.band_count} bands, CRS: {image_row.crs or 'None'})",
            status="completed",
            duration_ms=int((time.perf_counter() - t0) * 1000),
            output_summary=f"ID: {image_id}",
        )
    )

    # Step 2: VLM Inference (GeoChat-7B)
    t1 = time.perf_counter()
    vlm_result = geochat_adapter.vqa(image_path, question)
    raw_confidence = vlm_result.get("model_confidence", 0.85)

    steps.append(
        ExecutionStep(
            step_number=2,
            tool="geochat_vqa_inference",
            description=f"Executed remote sensing VQA prompt for question '{question}'",
            status="completed",
            duration_ms=int((time.perf_counter() - t1) * 1000),
            model="GeoChat-7B",
            output_summary=f"Model Certainty: {int(raw_confidence * 100)}%",
        )
    )

    # Step 3: Resolution & Confidence Evaluation
    t2 = time.perf_counter()
    x_res = 10.0
    y_res = 10.0
    if image_row.resolution and isinstance(image_row.resolution, dict):
        x_res = float(image_row.resolution.get("x_res", 10.0))
        y_res = float(image_row.resolution.get("y_res", 10.0))

    confidence = compute_vqa_confidence(
        model_confidence=raw_confidence,
        x_res=x_res,
        y_res=y_res,
    )

    steps.append(
        ExecutionStep(
            step_number=3,
            tool="evaluate_confidence_and_provenance",
            description=f"Calculated resolution-grounded confidence: {int(confidence.overall * 100)}%",
            status="completed",
            duration_ms=int((time.perf_counter() - t2) * 1000),
            output_summary=f"Overall: {confidence.overall}",
        )
    )

    # Step 4: Evidence Object Construction
    evidence = build_evidence(
        claim=vlm_result["answer"],
        source_analysis_id=job_id,
        source_image_ids=[image_id],
        model_used="geochat_7b",
        confidence=confidence,
        output_geometry=None,
        execution_steps=steps,
        artifacts=[image_row.preview_path] if image_row.preview_path else [],
    )

    # Step 5: Save Analysis Job Record
    job = AnalysisJob(
        id=job_id,
        aoi_id=image_row.aoi_id,
        task="single_image_vqa",
        status="completed",
        question=question,
        result={
            "answer": vlm_result["answer"],
            "model_confidence": raw_confidence,
            "evidence_id": evidence.id,
        },
        confidence=confidence.overall,
    )
    db.add(job)
    db.commit()

    return {
        "job_id": job_id,
        "image_id": image_id,
        "question": question,
        "answer": vlm_result["answer"],
        "confidence": confidence.to_dict(),
        "evidence": evidence.to_dict(),
        "execution_steps": [s.to_dict() for s in steps],
        "total_duration_ms": int((time.perf_counter() - start_total_t) * 1000),
    }
