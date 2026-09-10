"""Evidence and audit retrieval routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db import get_db
from ...models_db import AnalysisJob

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


@router.get("/{analysis_id}")
def get_evidence_by_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve evidence and execution trace associated with an analysis job."""
    job = db.get(AnalysisJob, analysis_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    res = job.result or {}
    return {
        "analysis_id": job.id,
        "task": job.task,
        "status": job.status,
        "question": job.question,
        "confidence": job.confidence,
        "evidence_id": res.get("evidence_id"),
        "created_at": job.created_at,
    }
