"""
backend/api/routes/analysis.py

The single "ask a question about these images" endpoint. Thin wrapper
around SatQueryAgent -- all the actual agentic logic lives in
backend/agent/orchestrator.py so it stays testable without HTTP.
"""
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agent.orchestrator import SatQueryAgent, RoutingError
from backend.api.routes.images import UPLOAD_DIR

router = APIRouter()
_agent = SatQueryAgent()


class AnalysisRequest(BaseModel):
    query: str
    image_ids: List[str]
    image_modalities: Optional[List[str]] = None  # e.g. ["optical","sar"]
    threshold: Optional[float] = None


def _resolve_path(image_id: str) -> str:
    matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not matches:
        raise HTTPException(404, f"image_id '{image_id}' not found -- upload it first via /api/images/upload")
    return str(matches[0])


@router.post("")
async def analyze(req: AnalysisRequest):
    if not req.image_ids:
        raise HTTPException(400, "image_ids must contain at least one uploaded image_id")

    image_paths = [_resolve_path(iid) for iid in req.image_ids]

    try:
        response = _agent.handle_query(
            query=req.query,
            image_paths=image_paths,
            image_modalities=req.image_modalities,
            threshold=req.threshold,
        )
    except RoutingError as e:
        raise HTTPException(422, {
            "message": str(e),
            "task_attempted": e.decision.task.value,
            "validation_reasons": e.decision.validation.reasons,
        })
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "task": response.task,
        "routing_summary": response.routing_summary,
        "evidence": response.evidence,
        "total_latency_ms": response.total_latency_ms,
    }
