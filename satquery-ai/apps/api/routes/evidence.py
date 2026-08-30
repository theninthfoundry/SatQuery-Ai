from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Evidence

router = APIRouter()


@router.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {
        "claim": evidence.claim,
        "derived_from": evidence.derived_from_json,
        "confidence_breakdown": evidence.confidence_breakdown_json,
    }
