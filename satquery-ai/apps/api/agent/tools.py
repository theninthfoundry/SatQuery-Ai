"""
Stub tool implementations matching the PRD's tool registry (Section 8).

Every function here returns schema-correct, deterministic mock output so the
agent routing and API layer are fully testable before any real model is
wired in. Replace the body of each function with an actual model call —
the signature and output shape should not need to change.
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

from .tool_registry import tool


@tool(
    name="answer_visual_question",
    description="Answer a structured or open-ended question about a single image",
    input_schema={"image_id": "string", "question": "string"},
    output_schema={"answer": "string", "confidence": "float"},
)
def answer_visual_question(image_id: str, question: str) -> Dict[str, Any]:
    # TODO: replace with a real VLM / classifier call.
    return {
        "answer": f"[stub] answer for '{question}' on image {image_id}",
        "confidence": 0.5,
    }


@tool(
    name="detect_objects",
    description="Detect and count objects of a given class in a single image",
    input_schema={"image_id": "string", "object_class": "string"},
    output_schema={"count": "int", "boxes": "list[GeoJSON Feature]", "confidence": "float"},
)
def detect_objects(image_id: str, object_class: str) -> Dict[str, Any]:
    # TODO: replace with a real detector (e.g. a SpaceNet-pretrained model).
    count = random.randint(5, 50)
    return {"count": count, "boxes": [], "confidence": 0.7}


@tool(
    name="segment_landcover",
    description="Classify dominant land cover in a single image",
    input_schema={"image_id": "string"},
    output_schema={"classes": "dict[str, float]", "confidence": "float"},
)
def segment_landcover(image_id: str) -> Dict[str, Any]:
    # TODO: replace with a real segmentation model.
    return {"classes": {"built_up": 0.3, "vegetation": 0.5, "water": 0.2}, "confidence": 0.65}


@tool(
    name="detect_change",
    description="Detect and quantify change between two co-registered images of the same AOI",
    input_schema={"image_before_id": "string", "image_after_id": "string", "aoi_id": "string"},
    output_schema={
        "change_percent": "float",
        "changed_regions": "GeoJSON FeatureCollection",
        "model_confidence": "float",
    },
)
def detect_change(image_before_id: str, image_after_id: str, aoi_id: str) -> Dict[str, Any]:
    """
    Real model wired in (models/change/ — architecture + train.py + infer.py),
    no longer a stub. It still needs two things this Phase 0 skeleton hasn't
    built yet, and fails honestly rather than fabricating a number when
    either is missing:
      1. An actual file on disk at the registered image path — Phase 0's
         POST /images only stores metadata, no upload/storage flow exists yet.
      2. A trained checkpoint at models/change/checkpoints/best.pt — without
         real LEVIR-CD/OSCD (or ISRO/SAC) data and a GPU, this runs an
         untrained network; the response's "is_trained" field says so.
    """
    from ..db import SessionLocal
    from ..models import Image as ImageRow

    db = SessionLocal()
    try:
        before_row = db.get(ImageRow, image_before_id)
        after_row = db.get(ImageRow, image_after_id)
    finally:
        db.close()

    empty_result = {
        "change_percent": 0.0,
        "changed_regions": {"type": "FeatureCollection", "features": []},
        "model_confidence": 0.0,
    }

    if not before_row or not after_row:
        return {**empty_result, "answer": "One or both referenced images were not found in the database."}

    try:
        result = _change_detector().detect(before_row.path, after_row.path)
    except FileNotFoundError:
        return {
            **empty_result,
            "answer": (
                f"Registered image path(s) not found on disk ({before_row.path!r}, "
                f"{after_row.path!r}) — Phase 0 only stores image metadata, not files. "
                "Upload the actual imagery to a real path to enable this."
            ),
        }

    return {
        "change_percent": result["change_percent"],
        "changed_regions": result["changed_regions"],
        "model_confidence": result["model_confidence"],
        "is_trained": result["is_trained"],
    }


_detector_singleton = None


def _change_detector():
    """Lazy singleton so the (small) model loads once, not per-request."""
    global _detector_singleton
    if _detector_singleton is None:
        from models.change.infer import ChangeDetector

        _detector_singleton = ChangeDetector()
    return _detector_singleton


@tool(
    name="sar_corroborate",
    description=(
        "Cross-check an optical change result against a SAR backscatter proxy "
        "for the same AOI/date pair. This is corroboration, not fusion — see PRD 7.4."
    ),
    input_schema={"aoi_id": "string", "change_job_id": "string"},
    output_schema={"corroboration_score": "float", "available": "bool"},
)
def sar_corroborate(aoi_id: str, change_job_id: str) -> Dict[str, Any]:
    # TODO: replace with a real SAR log-ratio backscatter-change proxy.
    # If SAR data isn't usable for this AOI, return available=False rather
    # than fabricating a score (see PRD Section 10) — an honest "unavailable"
    # is worth more in a demo than an invented number.
    return {"corroboration_score": 0.82, "available": True}


@tool(
    name="calculate_area",
    description="Calculate the area in square metres of a GeoJSON geometry",
    input_schema={"geometry": "GeoJSON geometry"},
    output_schema={"area_m2": "float"},
)
def calculate_area(geometry: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: replace with a real Shapely/GeoPandas area calculation in the
    # source CRS's projected equivalent — never compute area in lat/lon degrees.
    return {"area_m2": 0.0}


def compute_confidence(
    model_confidence: float,
    registration_quality: float,
    sar_agreement: Optional[float] = None,
) -> float:
    """
    Combine measurable signals into one confidence score (PRD Section 10).
    This is a simple weighted average — replace the weights once you have
    labeled data to tune against, but never let this become an
    LLM-generated number.
    """
    if sar_agreement is None:
        weights = {"model": 0.6, "registration": 0.4}
        return round(
            model_confidence * weights["model"] + registration_quality * weights["registration"], 2
        )
    weights = {"model": 0.5, "registration": 0.3, "sar": 0.2}
    return round(
        model_confidence * weights["model"]
        + registration_quality * weights["registration"]
        + sar_agreement * weights["sar"],
        2,
    )
