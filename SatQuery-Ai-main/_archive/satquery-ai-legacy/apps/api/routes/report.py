from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Report

router = APIRouter()


@router.post("/report/{aoi_id}")
def generate_report(aoi_id: str, db: Session = Depends(get_db)):
    # TODO: replace with a real PDF/GeoJSON export (PRD Section 17, reporting service).
    report = Report(aoi_id=aoi_id, file_path=None)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "status": "generated (stub — no file written yet)"}
