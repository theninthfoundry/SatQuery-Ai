from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..agent import route_query
from ..db import get_db
from ..models import Evidence, Image
from ..schemas import QueryRequest, QueryResponse

router = APIRouter()


def _resolve_image_context(aoi_id: str, db: Session) -> Dict[str, Any]:
    """
    Minimal, real (not stubbed) context resolution: pull the most recently
    registered image(s) for this AOI, filtered to sensor='optical' — this
    matters now that SAR images can also be registered for the same AOI
    (sar_corroborate resolves its own SAR pair separately, in tools.py).
    Without this filter, a registered SAR image could silently get fed
    into detect_change as if it were optical.
    """
    images = (
        db.query(Image)
        .filter(Image.aoi_id == aoi_id, Image.sensor == "optical")
        .order_by(desc(Image.acquisition_date))
        .all()
    )
    context: Dict[str, Any] = {"aoi_id": aoi_id}
    if images:
        context["image_id"] = images[0].id
    if len(images) >= 2:
        context["image_after_id"] = images[0].id
        context["image_before_id"] = images[1].id
    return context


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    context = _resolve_image_context(req.aoi_id, db)
    routed = route_query(req.question, context)

    confidence: Optional[float] = None
    if "error" in routed:
        # Insufficient context is a legitimate answer (PRD Section 10) —
        # surface it as-is rather than falling through to a phrased
        # "None" answer from an empty result dict.
        answer = routed["answer"]
    else:
        result = routed.get("result", {})
        answer = result.get("answer") or _phrase_answer(routed["tool_called"], result)
        confidence = result.get("confidence") or result.get("model_confidence")

    evidence = Evidence(
        claim=answer,
        derived_from_json={"tool": routed["tool_called"], "context": context},
        confidence_breakdown_json={"model_confidence": confidence},
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return QueryResponse(answer=answer, tool_called=routed["tool_called"], evidence_id=evidence.id)


def _phrase_answer(tool_name: str, result: dict) -> str:
    """Compose a sentence from tool facts. Never invent a number here."""
    if tool_name == "detect_change":
        answer = f"Change of {result.get('change_percent')}% detected in this AOI."
        if result.get("is_trained") is False:
            answer += " Note: the change model is untrained — this number is not yet meaningful."
        return answer
    if tool_name == "detect_objects":
        answer = f"{result.get('count')} objects detected."
        if result.get("is_trained") is False:
            answer += " Note: the object-count model is untrained — this number is not yet meaningful."
        return answer
    if tool_name == "segment_landcover":
        answer = f"Dominant land cover breakdown: {result.get('classes')}."
        if result.get("is_trained") is False:
            answer += " Note: the land-cover model is untrained — this breakdown is not yet meaningful."
        return answer
    if tool_name == "sar_corroborate":
        if result.get("available"):
            answer = (
                f"SAR corroboration score: {result.get('corroboration_score')} "
                f"(SAR change: {result.get('sar_change_percent')}%, "
                f"optical change: {result.get('optical_change_percent')}%)."
            )
            if result.get("optical_is_trained") is False:
                answer += (
                    " Note: the optical change model is untrained, so this score reflects "
                    "disagreement with a meaningless optical number, not a real SAR/optical mismatch."
                )
            return answer
        return "SAR corroboration unavailable for this AOI."
    return result.get("answer", "I don't have enough information to answer that confidently.")
