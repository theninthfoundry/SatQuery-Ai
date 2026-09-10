"""Query Capability Planner for structured semantic intent decomposition.

Separates semantic orchestration from deterministic GIS computation:
1. Natural language query -> QueryPlan (intent, target phenomena, operation, measurement).
2. The orchestrator dispatches the appropriate scientific engine (e.g. WaterBodyAnalyzer).
3. The scientific engine executes measurements and extracts vector geometries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class QueryPlan:
    """Structured execution plan derived from user query."""
    intent: str  # spatial_ranking, visual_grounding, single_image_vqa, bi_temporal_change, spectral_measurement, cross_modal_fusion
    target: str  # water_body, built_up, vegetation, building, general_landcover
    operation: str  # largest, smallest, count, describe, compare, locate, measure_area
    measurement: Optional[str] = "area"  # area, change_percent, count, spectral_index
    geometry_required: bool = True
    temporal_required: bool = False
    sensors: List[str] = field(default_factory=lambda: ["optical"])
    preferred_tools: List[str] = field(default_factory=list)
    fallback_policy: str = "abstain_if_unsupported"
    routing_score: float = 1.0
    routing_reason: str = "Deterministic pattern match"
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "target": self.target,
            "operation": self.operation,
            "measurement": self.measurement,
            "geometry_required": self.geometry_required,
            "temporal_required": self.temporal_required,
            "sensors": self.sensors,
            "preferred_tools": self.preferred_tools,
            "fallback_policy": self.fallback_policy,
            "routing_score": self.routing_score,
            "routing_reason": self.routing_reason,
            "matched_patterns": self.matched_patterns,
        }


class QueryCapabilityPlanner:
    """Decomposes natural language queries into capability-driven scientific plans."""

    SUPERLATIVE_LARGEST = [
        r"\blargest\b", r"\bbiggest\b", r"\bmajor\b", r"\bmaximum\b",
        r"\bmost extensive\b", r"\bhighest area\b", r"\bprimary\b"
    ]
    SUPERLATIVE_SMALLEST = [
        r"\bsmallest\b", r"\btiniest\b", r"\bminimum\b", r"\blowest area\b"
    ]

    TARGET_PATTERNS = {
        "water_body": [
            r"\bwater\b", r"\bwaterbody\b", r"\bwater body\b", r"\briver(s)?\b",
            r"\blake(s)?\b", r"\breservoir(s)?\b", r"\bpond(s)?\b", r"\bstream(s)?\b"
        ],
        "built_up": [
            r"\bbuilt-up\b", r"\bbuilt up\b", r"\bbuilding(s)?\b", r"\burban\b",
            r"\bsettlement(s)?\b", r"\broad(s)?\b", r"\binfrastructure\b"
        ],
        "vegetation": [
            r"\bvegetation\b", r"\bforest(s)?\b", r"\btree(s)?\b", r"\bcrop(s)?\b",
            r"\bagricultur(e|al)\b", r"\bcanopy\b"
        ],
    }

    CHANGE_PATTERNS = [
        r"\bchang(e|ed|ing)\b", r"\bdiffer(ence|ent)\b", r"\bbefore and after\b",
        r"\bincreas(e|ed)\b", r"\bdecreas(e|ed)\b", r"\bexpand(ed|ing)?\b",
        r"\bgrowth\b", r"\blos(s|t)\b", r"\bsprawl\b",
    ]

    SAR_FUSION_PATTERNS = [
        r"\bsar\b", r"\bradar\b", r"\bsentinel-1\b", r"\bbackscatter\b",
        r"\bcorroborat(e|ion)\b", r"\bpolarimetr(y|ic)\b",
    ]

    GROUNDING_PATTERNS = [
        r"\bwhere is\b", r"\bwhere are\b", r"\blocat(e|ing|ion)\b",
        r"\bfind\b", r"\bdetect\b", r"\bhighlight\b", r"\bbounding box\b",
    ]

    def plan(
        self,
        query: str,
        available_assets_count: int = 1,
        has_sar: bool = False,
    ) -> QueryPlan:
        """Parse query string into structured QueryPlan."""
        q_lower = query.lower().strip()

        # 1. Identify target physical phenomenon
        target = "general_landcover"
        matched_targets = []
        for phenom, patterns in self.TARGET_PATTERNS.items():
            matches = [p for p in patterns if re.search(p, q_lower)]
            if matches:
                target = phenom
                matched_targets.extend(matches)
                break

        # 2. Check for ranking superlatives (largest, smallest, etc.)
        is_largest = any(re.search(p, q_lower) for p in self.SUPERLATIVE_LARGEST)
        is_smallest = any(re.search(p, q_lower) for p in self.SUPERLATIVE_SMALLEST)
        has_change = any(re.search(p, q_lower) for p in self.CHANGE_PATTERNS)
        has_sar_query = any(re.search(p, q_lower) for p in self.SAR_FUSION_PATTERNS) or has_sar
        has_grounding = any(re.search(p, q_lower) for p in self.GROUNDING_PATTERNS)

        # 3. Decision Tree: Spatial Ranking takes priority when superlative + target is present
        if (is_largest or is_smallest) and target != "general_landcover":
            op = "largest" if is_largest else "smallest"
            preferred = ["WaterBodyAnalyzer"] if target == "water_body" else ["SpatialRankingEngine"]
            return QueryPlan(
                intent="spatial_ranking",
                target=target,
                operation=op,
                measurement="area",
                geometry_required=True,
                temporal_required=False,
                sensors=["optical"],
                preferred_tools=preferred,
                fallback_policy="abstain_if_unsupported",
                routing_score=1.0,
                routing_reason=f"Superlative '{op}' and target '{target}' matched deterministic spatial ranking pipeline",
                matched_patterns=matched_targets,
            )

        # 4. Bi-Temporal Change & Compound Investigation
        if has_change or available_assets_count >= 2:
            sensors = ["optical", "sar"] if has_sar_query else ["optical"]
            return QueryPlan(
                intent="bi_temporal_change" if not has_sar_query else "cross_modal_fusion",
                target=target if target != "general_landcover" else "built_up",
                operation="compare",
                measurement="change_percent",
                geometry_required=True,
                temporal_required=True,
                sensors=sensors,
                preferred_tools=["ChangeNetModelAdapter", "SpectralIndexCalculator", "SpatialFusionEngine"],
                fallback_policy="classical_fallback",
                routing_score=1.0,
                routing_reason="Change pattern matched and multiple temporal observations available",
                matched_patterns=["change_keywords" if has_change else "multi_asset_context"],
            )

        # 5. Multimodal Optical + SAR Corroboration
        if has_sar_query:
            return QueryPlan(
                intent="cross_modal_fusion",
                target=target,
                operation="corroborate",
                measurement="area",
                geometry_required=True,
                temporal_required=False,
                sensors=["optical", "sar"],
                preferred_tools=["SARProcessor", "SpatialFusionEngine"],
                fallback_policy="classical_fallback",
                routing_score=1.0,
                routing_reason="Radar/SAR sensor keywords or context triggered Level 2 physical spatial corroboration",
                matched_patterns=["sar_keywords"],
            )

        # 6. Generic Visual Grounding
        if has_grounding:
            return QueryPlan(
                intent="visual_grounding",
                target=target,
                operation="locate",
                measurement="area",
                geometry_required=True,
                temporal_required=False,
                sensors=["optical"],
                preferred_tools=["GeoChatModelAdapter", "SAMModelAdapter"],
                fallback_policy="abstain_if_unsupported",
                routing_score=1.0,
                routing_reason="Referring expression or location pattern matched",
                matched_patterns=["grounding_keywords"],
            )

        # 7. Default Single-Image Semantic VQA
        return QueryPlan(
            intent="single_image_vqa",
            target=target,
            operation="describe",
            measurement=None,
            geometry_required=False,
            temporal_required=False,
            sensors=["optical"],
            preferred_tools=["GeoChatModelAdapter"],
            fallback_policy="classical_fallback",
            routing_score=1.0,
            routing_reason="Default single-image visual question answering fallback",
            matched_patterns=[],
        )


query_capability_planner = QueryCapabilityPlanner()
