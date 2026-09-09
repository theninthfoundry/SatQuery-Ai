"""
backend/api/routes/reports.py

Downloadable-report endpoints. The frontend passes back the full
`evidence` dict it already received from /api/analysis (no server-side
evidence store required for the MVP -- swap in a DB-backed lookup by
evidence id later without changing this contract).
"""
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.reports.exporters import export_geojson, export_csv, export_pdf_dossier

router = APIRouter()


class ExportRequest(BaseModel):
    evidence: Dict[str, Any]
    routing_summary: Optional[Dict[str, Any]] = None


@router.post("/geojson")
async def download_geojson(req: ExportRequest):
    path = export_geojson(req.evidence)
    return FileResponse(path, media_type="application/geo+json",
                         filename=Path(path).name)


@router.post("/csv")
async def download_csv(req: ExportRequest):
    path = export_csv(req.evidence)
    return FileResponse(path, media_type="text/csv", filename=Path(path).name)


@router.post("/pdf")
async def download_pdf(req: ExportRequest):
    path = export_pdf_dossier(req.evidence, req.routing_summary)
    media_type = "application/pdf" if path.endswith(".pdf") else "text/plain"
    return FileResponse(path, media_type=media_type, filename=Path(path).name)

