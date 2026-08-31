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
    """
    Real model wired in (models/landcover/ — architecture + train.py +
    infer.py). Same honest-failure pattern as detect_change: missing DB
    row or missing file on disk returns a clear "answer" explaining why,
    never a fabricated fraction breakdown.
    """
    from ..db import SessionLocal
    from ..models import Image as ImageRow

    db = SessionLocal()
    try:
        image_row = db.get(ImageRow, image_id)
    finally:
        db.close()

    if not image_row:
        return {
            "classes": {},
            "confidence": 0.0,
            "answer": "Referenced image was not found in the database.",
        }

    try:
        result = _landcover_classifier().classify(image_row.path)
    except FileNotFoundError:
        return {
            "classes": {},
            "confidence": 0.0,
            "answer": (
                f"Registered image path {image_row.path!r} not found on disk — "
                "Phase 0 only stores image metadata, not files."
            ),
        }

    return result


_landcover_singleton = None


def _landcover_classifier():
    """Lazy singleton so the (small) model loads once, not per-request."""
    global _landcover_singleton
    if _landcover_singleton is None:
        from models.landcover.infer import LandCoverClassifier

        _landcover_singleton = LandCoverClassifier()
    return _landcover_singleton


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
        "Cross-check an optical change result against a real SAR backscatter "
        "change proxy for the same AOI. This is corroboration, not fusion — "
        "see PRD 7.4. Resolves its own SAR image pair for the AOI (independent "
        "of whatever optical images detect_change is using)."
    ),
    input_schema={"aoi_id": "string"},
    output_schema={
        "corroboration_score": "float",
        "available": "bool",
        "sar_change_percent": "float",
    },
)
def sar_corroborate(aoi_id: str) -> Dict[str, Any]:
    """
    Real implementation, no learned model involved (models/sar/proxy.py is
    a deterministic log-ratio statistic, not something that gets trained).
    Schema note: the original stub declared change_job_id as an input —
    dropped here. There's no persisted AnalysisJob/change-result table yet
    to resolve a job ID against, so this resolves both the SAR and optical
    image pairs directly from the AOI instead. Add change_job_id back once
    analysis jobs are actually persisted (PRD Section 12).
    """
    from sqlalchemy import desc

    from ..db import SessionLocal
    from ..models import Image as ImageRow

    db = SessionLocal()
    try:
        sar_images = (
            db.query(ImageRow)
            .filter(ImageRow.aoi_id == aoi_id, ImageRow.sensor == "sar")
            .order_by(desc(ImageRow.acquisition_date))
            .limit(2)
            .all()
        )
        optical_images = (
            db.query(ImageRow)
            .filter(ImageRow.aoi_id == aoi_id, ImageRow.sensor == "optical")
            .order_by(desc(ImageRow.acquisition_date))
            .limit(2)
            .all()
        )
    finally:
        db.close()

    unavailable = {"corroboration_score": 0.0, "available": False, "sar_change_percent": 0.0}

    if len(sar_images) < 2:
        return {
            **unavailable,
            "answer": "SAR corroboration unavailable — fewer than two SAR images are registered for this AOI.",
        }

    sar_after, sar_before = sar_images[0], sar_images[1]  # ordered most-recent-first
    try:
        sar_result = _sar_proxy().compute(sar_before.path, sar_after.path)
    except FileNotFoundError:
        return {**unavailable, "answer": "Registered SAR image path(s) not found on disk."}

    if len(optical_images) < 2:
        return {
            **unavailable,
            "sar_change_percent": sar_result["sar_change_percent"],
            "answer": (
                f"SAR-only signal: {sar_result['sar_change_percent']}% of the AOI shows a "
                "backscatter change, but no optical pair is registered to corroborate it against."
            ),
        }

    optical_after, optical_before = optical_images[0], optical_images[1]
    try:
        optical_result = _change_detector().detect(optical_before.path, optical_after.path)
    except FileNotFoundError:
        return {
            **unavailable,
            "sar_change_percent": sar_result["sar_change_percent"],
            "answer": (
                f"SAR-only signal: {sar_result['sar_change_percent']}% — registered optical "
                "image path(s) not found on disk."
            ),
        }

    # Corroboration = 1 minus the normalized gap between two *independent*
    # change estimates. This is not spatial polygon overlap (that needs
    # persisted per-AOI analysis jobs — see PRD Open Questions) — it's an
    # honest, simple agreement measure between two separately-computed
    # change percentages, not a fabricated "agreement" number.
    gap = abs(sar_result["sar_change_percent"] - optical_result["change_percent"]) / 100
    corroboration_score = round(max(0.0, 1 - gap), 2)

    return {
        "corroboration_score": corroboration_score,
        "available": True,
        "sar_change_percent": sar_result["sar_change_percent"],
        "optical_change_percent": optical_result["change_percent"],
        "optical_is_trained": optical_result["is_trained"],
    }


_sar_proxy_singleton = None


def _sar_proxy():
    global _sar_proxy_singleton
    if _sar_proxy_singleton is None:
        from models.sar.proxy import SARChangeProxy

        _sar_proxy_singleton = SARChangeProxy()
    return _sar_proxy_singleton


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
