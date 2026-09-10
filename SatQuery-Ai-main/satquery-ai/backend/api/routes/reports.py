"""Report download and audit dossier endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ...db import get_db
from ...models_db import AnalysisJob
from ...reports import (
    generate_pdf_report,
    generate_geojson_report,
    generate_csv_report,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{job_id}/pdf")
def download_pdf_report(job_id: str, db: Session = Depends(get_db)):
    """Download analysis mission report as a structured PDF dossier."""
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    pdf_bytes = generate_pdf_report(job)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="satquery_report_{job_id}.pdf"'},
    )


@router.get("/{job_id}/geojson")
def download_geojson_report(job_id: str, db: Session = Depends(get_db)):
    """Download analysis detection and change polygons as a GeoJSON FeatureCollection."""
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    geojson_data = generate_geojson_report(job)
    return geojson_data


@router.get("/{job_id}/csv")
def download_csv_report(job_id: str, db: Session = Depends(get_db)):
    """Download analysis metrics and cluster properties as a CSV spreadsheet."""
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    csv_text = generate_csv_report(job)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="satquery_metrics_{job_id}.csv"'},
    )
