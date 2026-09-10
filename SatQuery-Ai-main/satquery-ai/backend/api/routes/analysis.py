"""Analysis endpoints for Single-Image VQA, Visual Grounding, Bi-Temporal Change, and Optical+SAR Multimodal Fusion."""

from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...config import settings
from ...db import get_db
from ...models_db import AnalysisJob
from ...pipelines import (
    run_single_image_vqa_pipeline,
    run_visual_grounding_pipeline,
    run_bitemporal_change_pipeline,
    run_optical_sar_pipeline,
)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


class VQARequest(BaseModel):
    image_id: str
    question: str


class GroundingRequest(BaseModel):
    image_id: str
    referring_expression: str


class ChangeAnalysisRequest(BaseModel):
    image_before_id: str
    image_after_id: str
    aoi_id: Optional[str] = None
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class OpticalSARAnalysisRequest(BaseModel):
    optical_image_id: str
    sar_image_id: str
    aoi_id: Optional[str] = None


class SpatialRankRequest(BaseModel):
    image_id: str = "active_image"
    image_path: Optional[str] = None
    target: str = "water_body"
    operation: str = "largest"
    aoi_id: Optional[str] = None
    query: Optional[str] = ""
    expected_source_image_id: Optional[str] = None
    min_area_m2: float = 500.0


@router.post("/vqa")
def analyze_vqa(payload: VQARequest, db: Session = Depends(get_db)):
    """Execute single-image remote-sensing VQA with verifiable evidence generation."""
    try:
        result = run_single_image_vqa_pipeline(
            image_id=payload.image_id,
            question=payload.question,
            db=db,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"VQA pipeline execution failed: {str(e)}",
        )


@router.post("/grounding")
def analyze_grounding(payload: GroundingRequest, db: Session = Depends(get_db)):
    """Execute visual grounding for a referring expression, returning real-world GeoJSON polygons."""
    try:
        result = run_visual_grounding_pipeline(
            image_id=payload.image_id,
            referring_expression=payload.referring_expression,
            db=db,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visual grounding pipeline failed: {str(e)}",
        )


@router.post("/change")
def analyze_change(payload: ChangeAnalysisRequest, db: Session = Depends(get_db)):
    """Execute bi-temporal change detection and real ground area quantification."""
    try:
        result = run_bitemporal_change_pipeline(
            image_before_id=payload.image_before_id,
            image_after_id=payload.image_after_id,
            aoi_id=payload.aoi_id,
            threshold=payload.threshold,
            db=db,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change detection pipeline failed: {str(e)}",
        )


@router.post("/optical-sar")
def analyze_optical_sar(payload: OpticalSARAnalysisRequest, db: Session = Depends(get_db)):
    """Execute optical + SAR multimodal feature extraction and cross-modal corroboration."""
    try:
        result = run_optical_sar_pipeline(
            optical_image_id=payload.optical_image_id,
            sar_image_id=payload.sar_image_id,
            aoi_id=payload.aoi_id,
            db=db,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optical+SAR multimodal pipeline failed: {str(e)}",
        )


@router.post("/spatial-rank")
def analyze_spatial_rank(payload: SpatialRankRequest, db: Session = Depends(get_db)):
    """Execute deterministic spatial ranking (e.g. largest water body) with geodesic contour polygonization."""
    try:
        from ...engines.spatial_ranking import spatial_ranking_engine

        if payload.image_path:
            result = spatial_ranking_engine.execute(
                image_path=payload.image_path,
                target=payload.target,
                operation=payload.operation,
                image_id=payload.image_id,
                expected_source_image_id=payload.expected_source_image_id,
                min_area_m2=payload.min_area_m2,
            )
        else:
            result = spatial_ranking_engine.rank(
                image_id=payload.image_id,
                target=payload.target,
                operation=payload.operation,
                db=db,
                query=payload.query or f"Find {payload.operation} {payload.target}",
                aoi_id=payload.aoi_id,
                expected_source_image_id=payload.expected_source_image_id,
            )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial ranking analysis failed: {str(e)}",
        )


@router.get("/{job_id}/mask")
def get_change_mask_preview(job_id: str):
    """Serve the generated binary/color change mask overlay PNG."""
    mask_path = Path(settings.preview_dir) / f"{job_id}_mask.png"
    if not mask_path.exists():
        raise HTTPException(status_code=404, detail="Change mask preview not found")
    return FileResponse(mask_path, media_type="image/png")


@router.get("/{job_id}")
def get_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Retrieve an analysis job by ID."""
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return {
        "id": job.id,
        "aoi_id": job.aoi_id,
        "task": job.task,
        "status": job.status,
        "question": job.question,
        "result": job.result,
        "confidence": job.confidence,
        "created_at": job.created_at,
    }


@router.post("/{job_id}/replay")
def replay_analysis_endpoint(job_id: str):
    """Replay historical analysis and verify exact scientific reproducibility."""
    try:
        from scripts.reproduce_analysis import reproduce_analysis
        report = reproduce_analysis(job_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay execution failed: {str(e)}")
