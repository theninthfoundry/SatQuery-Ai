"""
Fail-closed contracts for GeoChat VQA / grounding.

Per audit section 18: when the model is absent or not READY, the route
must return this exact shape — never a plausible rectangle, never a
confident-sounding caption. This module is the only place allowed to
construct a "model absent" response, so every caller gets the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.models.registry import ModelNotReadyError, ModelRegistry


@dataclass
class GroundingResult:
    boxes: list[dict[str, Any]]
    model_confidence: Optional[float]
    fallback_used: bool
    execution_mode: str          # "model_inference" | "offline_fallback"
    model_id: Optional[str] = None
    checkpoint_sha256: Optional[str] = None


@dataclass
class VQAResult:
    answer: Optional[str]
    model_confidence: Optional[float]
    fallback_used: bool
    execution_mode: str
    model_id: Optional[str] = None
    checkpoint_sha256: Optional[str] = None


def offline_fallback_grounding() -> GroundingResult:
    return GroundingResult(
        boxes=[],
        model_confidence=None,
        fallback_used=True,
        execution_mode="offline_fallback",
    )


def offline_fallback_vqa() -> VQAResult:
    return VQAResult(
        answer=None,
        model_confidence=None,
        fallback_used=True,
        execution_mode="offline_fallback",
    )


def run_grounding(
    registry: ModelRegistry,
    model_id: str,
    infer_fn,
    *args,
    **kwargs,
) -> GroundingResult:
    """
    Wrap any real grounding inference call. If the model isn't READY,
    this returns the fail-closed contract instead of raising past the
    API boundary and instead of letting a caller improvise a guess.

    `infer_fn` must be the actual model call — this function does not
    perform inference itself, it only gates access to it.
    """
    try:
        entry = registry.assert_ready(model_id)
    except ModelNotReadyError:
        return offline_fallback_grounding()

    boxes, model_confidence = infer_fn(*args, **kwargs)
    return GroundingResult(
        boxes=boxes,
        model_confidence=model_confidence,
        fallback_used=False,
        execution_mode="model_inference",
        model_id=model_id,
        checkpoint_sha256=entry.checkpoint_sha256,
    )


def run_vqa(
    registry: ModelRegistry,
    model_id: str,
    infer_fn,
    *args,
    **kwargs,
) -> VQAResult:
    try:
        entry = registry.assert_ready(model_id)
    except ModelNotReadyError:
        return offline_fallback_vqa()

    answer, model_confidence = infer_fn(*args, **kwargs)
    return VQAResult(
        answer=answer,
        model_confidence=model_confidence,
        fallback_used=False,
        execution_mode="model_inference",
        model_id=model_id,
        checkpoint_sha256=entry.checkpoint_sha256,
    )
