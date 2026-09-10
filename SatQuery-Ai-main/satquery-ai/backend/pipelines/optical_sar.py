"""Optical + SAR Multimodal Analysis and Cross-Modal Corroboration Pipeline."""

import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models_db import ImageRecord, AnalysisJob
from ..models.dofa import dofa_adapter
from ..evidence import (
    build_evidence,
    compute_multimodal_confidence,
    ExecutionStep,
    EvidenceObject,
)


def validate_cross_modal_pair(
    optical_row: ImageRecord,
    sar_row: ImageRecord,
) -> Tuple[bool, float, List[str]]:
    """Validate spatial overlap and sensor complementarity between an Optical and SAR asset."""
    warnings: List[str] = []
    
    # Check modalities
    opt_mod = (optical_row.modality or "").lower()
    sar_mod = (sar_row.modality or "").lower()

    if "sar" in opt_mod and "optical" in sar_mod:
        # Swap if accidentally reversed
        optical_row, sar_row = sar_row, optical_row
    elif "sar" not in sar_mod and sar_row.band_count > 2 and optical_row.band_count > 2:
        warnings.append("Neither image has explicit SAR tags; running dual-sensor comparison.")

    # Spatial overlap calculation — Zero Fabrication
    b_bounds = optical_row.bounds
    a_bounds = sar_row.bounds

    if not b_bounds or not a_bounds or not isinstance(b_bounds, dict) or not isinstance(a_bounds, dict):
        warnings.append("Missing bounding box metadata for one or both images.")
        return False, 0.0, warnings

    req_keys = ("min_lon", "min_lat", "max_lon", "max_lat")
    if not all(k in b_bounds for k in req_keys) or not all(k in a_bounds for k in req_keys):
        warnings.append("Incomplete bounding box coordinates.")
        return False, 0.0, warnings

    iou_score = 0.0
    try:
        from shapely.geometry import box
        poly_opt = box(b_bounds["min_lon"], b_bounds["min_lat"], b_bounds["max_lon"], b_bounds["max_lat"])
        poly_sar = box(a_bounds["min_lon"], a_bounds["min_lat"], a_bounds["max_lon"], a_bounds["max_lat"])

        if not poly_opt.intersects(poly_sar):
            warnings.append("Images have no geographic overlap (disjoint bounds).")
            return False, 0.0, warnings

        inter_area = poly_opt.intersection(poly_sar).area
        union_area = poly_opt.union(poly_sar).area
        if union_area <= 1e-12:
            warnings.append("Zero area bounding boxes.")
            return False, 0.0, warnings

        iou_score = round(float(inter_area / union_area), 4)
    except Exception as e:
        warnings.append(f"Spatial overlap calculation error: {e}")
        return False, 0.0, warnings

    is_valid = iou_score > 0.05
    if not is_valid:
        warnings.append(f"Geographic overlap too small (IoU {iou_score:.4f} <= 0.05).")

    return is_valid, iou_score, warnings


def run_optical_sar_pipeline(
    optical_image_id: str,
    sar_image_id: str,
    db: Session,
    aoi_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the end-to-end Optical + SAR Multimodal Analysis and Corroboration Pipeline."""
    steps = []
    job_id = f"job_fusion_{uuid.uuid4().hex[:10]}"
    start_total_t = time.perf_counter()

    # Step 1: Retrieve cross-modal assets
    t0 = time.perf_counter()
    optical_row = db.get(ImageRecord, optical_image_id)
    sar_row = db.get(ImageRecord, sar_image_id)

    if not optical_row or not sar_row:
        raise ValueError("One or both specified cross-modal assets were not found in the database.")

    optical_path = Path(optical_row.path)
    sar_path = Path(sar_row.path)

    if not optical_path.exists() or not sar_path.exists():
        raise FileNotFoundError(f"Image raster(s) not found on disk ({optical_path}, {sar_path})")

    is_valid, reg_quality, warnings = validate_cross_modal_pair(optical_row, sar_row)
    steps.append(
        ExecutionStep(
            step_number=1,
            tool="retrieve_cross_modal_assets",
            description=f"Loaded Optical: {optical_row.filename} & SAR: {sar_row.filename} (Spatial Overlap IoU: {int(reg_quality * 100)}%)",
            status="completed" if is_valid else "failed",
            duration_ms=int((time.perf_counter() - t0) * 1000),
            output_summary=f"IoU: {reg_quality}",
        )
    )

    # Fail fast with honest abstention if spatial overlap is insufficient
    if not is_valid:
        from ..evidence import MultimodalConfidence
        abstain_rationale = f"Abstained from cross-modal fusion: Insufficient spatial overlap (IoU={reg_quality:.2f}). {'; '.join(warnings)}"
        confidence = MultimodalConfidence(
            model=0.0,
            spatial_agreement=0.0,
            resolution_suitability=0.0,
            registration_quality=reg_quality,
            cloud_freedom=1.0,
            overall=0.0,
            rationale=abstain_rationale,
        )
        evidence = build_evidence(
            claim=abstain_rationale,
            source_analysis_id=job_id,
            source_image_ids=[optical_image_id, sar_image_id],
            model_used="none",
            confidence=confidence,
            output_geometry=None,
            execution_steps=steps,
            artifacts=[optical_row.preview_path, sar_row.preview_path],
        )
        job = AnalysisJob(
            id=job_id,
            aoi_id=aoi_id or optical_row.aoi_id,
            task="optical_sar_fusion",
            status="abstained",
            question="Cross-modal optical and SAR joint analysis",
            result={
                "decision": "ABSTAIN",
                "reason": "SPATIAL_OVERLAP_INSUFFICIENT",
                "corroboration_score": 0.0,
                "joint_claim": evidence.claim,
                "optical_features": None,
                "sar_features": None,
                "evidence_id": evidence.id,
                "warnings": warnings,
            },
            confidence=0.0,
        )
        db.add(job)
        db.commit()

        return {
            "job_id": job_id,
            "decision": "ABSTAIN",
            "reason": "SPATIAL_OVERLAP_INSUFFICIENT",
            "optical_image_id": optical_image_id,
            "sar_image_id": sar_image_id,
            "corroboration_score": 0.0,
            "joint_claim": evidence.claim,
            "optical_features": None,
            "sar_features": None,
            "confidence": confidence.to_dict(),
            "evidence": evidence.to_dict(),
            "execution_steps": [s.to_dict() for s in steps],
            "total_duration_ms": int((time.perf_counter() - start_total_t) * 1000),
            "execution_mode": "abstained",
            "model": None,
            "learned_fusion": False,
        }

    # Step 2: Cross-Modal Feature Extraction & Corroboration
    t1 = time.perf_counter()
    fusion_result = dofa_adapter.fuse_and_corroborate(optical_path, sar_path)
    corroboration_score = fusion_result["corroboration_score"]
    model_conf = fusion_result.get("model_confidence", corroboration_score)
    is_real_weights = fusion_result.get("is_real_weights", False)

    steps.append(
        ExecutionStep(
            step_number=2,
            tool="dofa_multimodal_feature_extraction" if is_real_weights else "physical_spatial_corroboration",
            description=(
                f"Extracted wavelength-conditioned embeddings (Optical {optical_row.band_count}-band & SAR {fusion_result['sar_features']['polarization']})"
                if is_real_weights
                else f"Computed deterministic physical cross-modal corroboration (Optical spectral reflectance & SAR radar backscatter; DOFA weights offline)"
            ),
            status="completed",
            duration_ms=int((time.perf_counter() - t1) * 1000),
            model="DOFA-ViT-Base" if is_real_weights else None,
            output_summary=f"Corroboration: {int(corroboration_score * 100)}% ({'Learned DOFA Fusion' if is_real_weights else 'Level 2 Physical Corroboration'})",
        )
    )

    # Step 3: Multimodal Confidence Engine
    t2 = time.perf_counter()
    x_res = 10.0
    y_res = 10.0
    if optical_row.resolution and isinstance(optical_row.resolution, dict):
        x_res = float(optical_row.resolution.get("x_res", 10.0))
        y_res = float(optical_row.resolution.get("y_res", 10.0))

    confidence = compute_multimodal_confidence(
        model_confidence=model_conf,
        registration_quality=reg_quality,
        sar_agreement=corroboration_score,
        x_res=x_res,
        y_res=y_res,
    )

    steps.append(
        ExecutionStep(
            step_number=3,
            tool="evaluate_cross_modal_confidence",
            description=f"Calculated multimodal confidence: {int(confidence.overall * 100)}% (SAR agreement: {int(corroboration_score * 100)}%)",
            status="completed",
            duration_ms=int((time.perf_counter() - t2) * 1000),
            output_summary=f"Overall: {confidence.overall}",
        )
    )

    # Step 4: Construct Canonical Evidence
    model_used = "dofa_foundation_fusion" if is_real_weights else "deterministic_physical_corroboration"
    evidence = build_evidence(
        claim=fusion_result["joint_claim"],
        source_analysis_id=job_id,
        source_image_ids=[optical_image_id, sar_image_id],
        model_used=model_used,
        confidence=confidence,
        output_geometry=None,
        execution_steps=steps,
        artifacts=[optical_row.preview_path, sar_row.preview_path],
    )

    # Step 5: Save Analysis Job in DB
    job = AnalysisJob(
        id=job_id,
        aoi_id=aoi_id or optical_row.aoi_id,
        task="optical_sar_fusion",
        status="completed",
        question="Cross-modal optical and SAR joint analysis",
        result={
            "decision": "ANSWER",
            "corroboration_score": corroboration_score,
            "joint_claim": fusion_result["joint_claim"],
            "optical_features": fusion_result["optical_features"],
            "sar_features": fusion_result["sar_features"],
            "evidence_id": evidence.id,
            "execution_mode": "learned_fusion" if is_real_weights else "deterministic_cross_modal",
            "learned_fusion": is_real_weights,
            "model": "DOFA-ViT-Base" if is_real_weights else None,
        },
        confidence=confidence.overall,
    )
    db.add(job)
    db.commit()

    return {
        "job_id": job_id,
        "decision": "ANSWER",
        "optical_image_id": optical_image_id,
        "sar_image_id": sar_image_id,
        "corroboration_score": corroboration_score,
        "joint_claim": fusion_result["joint_claim"],
        "optical_features": fusion_result["optical_features"],
        "sar_features": fusion_result["sar_features"],
        "confidence": confidence.to_dict(),
        "evidence": evidence.to_dict(),
        "execution_steps": [s.to_dict() for s in steps],
        "total_duration_ms": int((time.perf_counter() - start_total_t) * 1000),
        "execution_mode": "learned_fusion" if is_real_weights else "deterministic_cross_modal",
        "learned_fusion": is_real_weights,
        "model": "DOFA-ViT-Base" if is_real_weights else None,
    }
