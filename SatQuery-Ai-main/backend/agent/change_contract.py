"""
Fail-closed ChangeNet wrapper (audit section 24).

Current ChangeNet is fallback/unverified until a real checkpoint passes
mark_verified() on the ModelRegistry. This module makes it structurally
impossible for the UI to say "ChangeNet detected 1.82 ha" while actually
running the classical fallback — the result object carries
model_name="classical_rgb_change_fallback" in that case, never
"ChangeNet".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from backend.core.observation import ObservationRecord, TemporalPairValidation, validate_temporal_pair
from backend.models.registry import ModelNotReadyError, ModelRegistry


class ChangeDetectionError(ValueError):
    pass


@dataclass
class ChangeResult:
    model_name: str                       # "changenet" | "classical_rgb_change_fallback"  # truthlock:allow -- field-shape doc, not a claim
    fallback_used: bool
    probability_map: Optional[Any]        # 2D array when model ran; None on fallback
    binary_mask: Optional[Any]
    change_area_m2: Optional[float]
    area_method: Optional[str]
    t1_observation_id: str
    t2_observation_id: str
    limitation_notes: list[str]


def run_change_detection(
    registry: ModelRegistry,
    model_id: str,
    t1: ObservationRecord,
    t2: ObservationRecord,
    *,
    changenet_infer_fn=None,
    classical_fallback_fn=None,
    pair_validation_kwargs: Optional[dict] = None,
) -> ChangeResult:
    """
    `changenet_infer_fn(t1, t2) -> (probability_map, binary_mask, change_area_m2, area_method)`
    `classical_fallback_fn(t1, t2) -> (binary_mask, change_area_m2, area_method)`

    Both are the caller's real implementations; this function only
    decides which is allowed to run and labels the result honestly.
    """
    pair_check: TemporalPairValidation = validate_temporal_pair(
        t1, t2, **(pair_validation_kwargs or {})
    )
    if not pair_check.ok:
        raise ChangeDetectionError(
            "Refusing to run change detection on an invalid temporal pair: "
            + "; ".join(pair_check.reasons)
        )

    try:
        registry.assert_ready(model_id)
        model_ready = True
    except ModelNotReadyError:
        model_ready = False

    if model_ready and changenet_infer_fn is not None:
        prob_map, binary_mask, area_m2, area_method = changenet_infer_fn(t1, t2)
        return ChangeResult(
            model_name="changenet",  # truthlock:allow -- reached only after registry.assert_ready() above
            fallback_used=False,
            probability_map=prob_map,
            binary_mask=binary_mask,
            change_area_m2=area_m2,
            area_method=area_method,
            t1_observation_id=t1.observation_id,
            t2_observation_id=t2.observation_id,
            limitation_notes=[],
        )

    if classical_fallback_fn is None:
        raise ChangeDetectionError(
            "ChangeNet is not READY and no classical_fallback_fn was provided; "
            "refusing to fabricate a change result."
        )

    binary_mask, area_m2, area_method = classical_fallback_fn(t1, t2)
    return ChangeResult(
        model_name="classical_rgb_change_fallback",
        fallback_used=True,
        probability_map=None,
        binary_mask=binary_mask,
        change_area_m2=area_m2,
        area_method=area_method,
        t1_observation_id=t1.observation_id,
        t2_observation_id=t2.observation_id,
        limitation_notes=[
            "ChangeNet checkpoint not verified/READY — this result is from "
            "classical RGB differencing, not neural change detection. "
            "Must be labeled 'Classical change fallback' in the UI, never "
            "attributed to ChangeNet."  # truthlock:allow -- this string is the fail-closed policy text itself
        ],
    )
