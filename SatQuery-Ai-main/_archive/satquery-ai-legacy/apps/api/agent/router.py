"""
Agent router: turns a natural-language question into one tool call.

Two modes are anticipated (only RULE_BASED is implemented here):
  - RULE_BASED (this file): keyword/regex intent matching. Reliable, fast,
    fully offline — good enough for a well-scoped demo, and a sane fallback
    for the other mode below.
  - LLM_ASSISTED (not yet implemented): prompt a local Ollama model (or
    Gemini, if online) to emit a JSON tool call, validated against the
    tool registry before execution. Most open models don't have a native
    function-calling API — this would be prompt-engineered structured
    output, parsed and schema-validated, never trusted blindly.

The router never lets an LLM interpret pixels or invent numbers; it only
ever selects which registered tool to call and with what arguments.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .tool_registry import registry

INTENT_PATTERNS: List[Tuple[str, str]] = [
    # Order matters: more specific / narrower intents are checked first so
    # a generic word like "change" inside a SAR question doesn't shadow it.
    (r"\bsar\b|\bcorroborat|\bdoes.*support\b|\bagree\b", "sar_corroborate"),
    (r"\bhow many\b|\bcount\b", "detect_objects"),
    (r"\bland cover\b|\bclassify\b|\bdominant\b", "segment_landcover"),
    (r"\bchanged?\b|\bincrease[d]?\b|\bdecrease[d]?\b|\bbetween\b.*\band\b", "detect_change"),
]


def classify_intent(question: str) -> str:
    q = question.lower()
    for pattern, tool_name in INTENT_PATTERNS:
        if re.search(pattern, q):
            return tool_name
    return "answer_visual_question"  # fallback: open VQA


def route_query(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    context carries whatever IDs are already known for this session, e.g.
    aoi_id / image_id / image_before_id / image_after_id. The router only
    forwards the fields the chosen tool actually declares in its
    input_schema.
    """
    tool_name = classify_intent(question)
    chosen_tool = registry.get(tool_name)

    kwargs = {k: v for k, v in context.items() if k in chosen_tool.input_schema}
    if tool_name == "answer_visual_question":
        kwargs["question"] = question

    missing = [k for k in chosen_tool.input_schema if k not in kwargs]
    if missing:
        return {
            "tool_called": tool_name,
            "error": f"insufficient context — missing {missing}",
            "answer": "I don't have enough information to answer that confidently yet.",
        }

    result = registry.call(tool_name, **kwargs)
    return {"tool_called": tool_name, "result": result}
