"""
backend/agent/router.py

Layer 1 (semantic intent) + Layer 2 (spatial/modality validation) of the
architecture diagram. Deliberately rule-based/keyword+regex rather than
an LLM call: it is fast, free, fully deterministic (reproducible smoke
tests), and auditable in the provenance trace -- exactly what a "3-layer
agent router" for a fixed tool registry should be. Swap in an LLM-based
classifier later without touching anything downstream, since the output
contract (RoutingDecision) stays the same.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from backend.agent.tool_registry import TaskType, get_tool, ToolSpec
from backend.geospatial.engine import RasterInfo, validate_bitemporal_pair, PairValidationResult


# ---------------------------------------------------------------------------
# Layer 1: intent classification
# ---------------------------------------------------------------------------

_INTENT_PATTERNS = [
    (TaskType.CHANGE_VQA, re.compile(
        r"\b(what|how much|has).*(chang|increas|decreas|differ)", re.I)),
    (TaskType.CHANGE_DETECTION, re.compile(
        r"\b(change detection|compare (these|the) two|between these two dates|"
        r"before and after)", re.I)),
    (TaskType.FUSION_OPTICAL_SAR, re.compile(
        r"\b(optical and sar|sar and optical|use.*(optical|sar).*together|"
        r"corroborate|cross[- ]modal)", re.I)),
    (TaskType.GROUNDING, re.compile(
        r"\b(highlight|locate|point out|where is|find the|mark the|show me the)\b", re.I)),
    (TaskType.CAPTIONING, re.compile(
        r"\b(describe|caption|summarize|overview of|scene description)\b", re.I)),
]

_DEFAULT_INTENT = TaskType.VQA


@dataclass
class IntentResult:
    task: TaskType
    matched_pattern: Optional[str]
    referring_expression: Optional[str] = None


def classify_intent(query: str, image_count: int) -> IntentResult:
    """Layer 1. Order matters: more specific intents (change/fusion) are
    checked before generic captioning/VQA. image_count acts as a prior --
    a 2-image request phrased ambiguously still routes to change/fusion
    rather than single-image VQA."""
    q = query.strip()

    for task, pattern in _INTENT_PATTERNS:
        m = pattern.search(q)
        if m:
            ref_expr = None
            if task == TaskType.GROUNDING:
                ref_expr = _extract_referring_expression(q)
            return IntentResult(task=task, matched_pattern=pattern.pattern, referring_expression=ref_expr)

    if image_count >= 2:
        # two images given but no strong keyword match -> default to
        # change-VQA since that's the most common 2-image ask
        return IntentResult(task=TaskType.CHANGE_VQA, matched_pattern=None)

    return IntentResult(task=_DEFAULT_INTENT, matched_pattern=None)


def _extract_referring_expression(query: str) -> str:
    """Best-effort extraction of "the X" after a grounding trigger word,
    e.g. 'Highlight the water reservoir' -> 'water reservoir'."""
    m = re.search(
        r"(?:highlight|locate|point out|find|mark|show me)\s+(?:the\s+)?(.+?)[\.\?!]?$",
        query, re.I,
    )
    return m.group(1).strip() if m else query


# ---------------------------------------------------------------------------
# Layer 2: input compatibility validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    is_valid: bool
    tool: ToolSpec
    reasons: list
    pair_check: Optional[PairValidationResult] = None


def validate_inputs(task: TaskType, rasters: list) -> ValidationResult:
    """Layer 2. `rasters` is a list of RasterInfo already produced by
    geospatial.engine.read_raster_info() -- this function never touches
    the filesystem itself, only checks counts/CRS/overlap."""
    tool = get_tool(task)
    reasons = []
    pair_check = None

    if len(rasters) != tool.required_image_count:
        reasons.append(
            f"Task '{task.value}' requires {tool.required_image_count} image(s), "
            f"got {len(rasters)}."
        )
        return ValidationResult(is_valid=False, tool=tool, reasons=reasons)

    for r in rasters:
        if r.crs_epsg is None:
            reasons.append(f"{r.path}: no CRS detected -- geodetic outputs will be unreliable.")

    if tool.requires_bitemporal and len(rasters) == 2:
        pair_check = validate_bitemporal_pair(rasters[0], rasters[1])
        if not pair_check.is_valid:
            reasons.extend(pair_check.reasons)

    is_valid = (pair_check is None or pair_check.is_valid) and not any(
        "requires" in r for r in reasons
    )
    return ValidationResult(is_valid=is_valid, tool=tool, reasons=reasons, pair_check=pair_check)


@dataclass
class RoutingDecision:
    intent: IntentResult
    validation: ValidationResult

    @property
    def task(self) -> TaskType:
        return self.intent.task

    @property
    def can_execute(self) -> bool:
        return self.validation.is_valid


def route(query: str, rasters: list) -> RoutingDecision:
    """Top-level entrypoint the orchestrator calls: query text + already
    -opened RasterInfo list -> a routing decision with pass/fail and
    reasons, before any model is touched."""
    intent = classify_intent(query, image_count=len(rasters))
    validation = validate_inputs(intent.task, rasters)
    return RoutingDecision(intent=intent, validation=validation)
