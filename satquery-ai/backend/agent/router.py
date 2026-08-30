"""Intent classification and query routing for remote sensing natural-language questions."""

import re
from enum import Enum
from typing import Dict, Any, Tuple, List, Optional


class IntentType(str, Enum):
    VQA = "vqa"
    GROUNDING = "grounding"
    CHANGE_DETECTION = "change_detection"
    OPTICAL_SAR_FUSION = "optical_sar_fusion"
    UNSUPPORTED = "unsupported"


GROUNDING_KEYWORDS = [
    "highlight",
    "locate",
    "box",
    "bounding box",
    "find the",
    "where is",
    "where are",
    "segment",
    "outline",
    "draw a box",
]

CHANGE_KEYWORDS = [
    "change",
    "changed",
    "alteration",
    "difference",
    "growth",
    "shrink",
    "before and after",
    "multitemporal",
    "temporal",
    "between the two",
    "what happened",
]

FUSION_KEYWORDS = [
    "corroborate",
    "sar",
    "radar",
    "backscatter",
    "polarization",
    "penetrate",
    "optical and sar",
    "sentinel-1",
    "sentinel 1",
    "cross-modal",
    "joint analysis",
]


def classify_intent(
    query: str,
    available_image_count: int = 1,
    has_sar: bool = False,
) -> Tuple[IntentType, float, Dict[str, Any]]:
    """Classify user natural-language remote sensing query into a structured execution intent."""
    q_lower = query.lower().strip()
    extracted_params: Dict[str, Any] = {}

    if not q_lower:
        return IntentType.UNSUPPORTED, 0.0, {"reason": "Empty query"}

    # 1. Check Change Detection intent
    if any(k in q_lower for k in CHANGE_KEYWORDS):
        if available_image_count >= 2:
            return IntentType.CHANGE_DETECTION, 0.95, {"task": "bi_temporal_change"}
        return IntentType.CHANGE_DETECTION, 0.80, {
            "task": "bi_temporal_change",
            "warning": "Requires 2 images (before and after)",
        }

    # 2. Check Optical + SAR Fusion intent
    if any(k in q_lower for k in FUSION_KEYWORDS) or has_sar:
        return IntentType.OPTICAL_SAR_FUSION, 0.92, {"task": "optical_sar_fusion"}

    # 3. Check Visual Grounding intent
    for k in GROUNDING_KEYWORDS:
        if k in q_lower:
            # Extract target expression
            expr = q_lower
            if "highlight " in q_lower:
                expr = q_lower.split("highlight ", 1)[1]
            elif "locate " in q_lower:
                expr = q_lower.split("locate ", 1)[1]
            elif "find " in q_lower:
                expr = q_lower.split("find ", 1)[1]
            
            extracted_params["referring_expression"] = expr.strip()
            return IntentType.GROUNDING, 0.90, extracted_params

    # 4. Default to Single-Image VQA (Descriptive, land cover, object counting)
    return IntentType.VQA, 0.88, {"task": "single_image_vqa", "question": query}
