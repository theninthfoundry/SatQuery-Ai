"""Structured mission specification parser for remote sensing queries.

Extracts mission objectives, target physical phenomena, temporal scope,
required sensor modalities, and scientific constraints from natural language.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class MissionIntent(str, Enum):
    """Core perceptual and analytical intent of the query."""
    SINGLE_IMAGE_VQA = "single_image_vqa"
    VISUAL_GROUNDING = "visual_grounding"
    SPATIAL_RANKING = "spatial_ranking"
    TEMPORAL_CHANGE = "temporal_change"
    CROSS_MODAL_FUSION = "cross_modal_fusion"
    COMPOUND_INVESTIGATION = "compound_investigation"
    SPECTRAL_INSPECTION = "spectral_inspection"
    SAR_ANALYSIS = "sar_analysis"
    UNKNOWN = "unknown"


class TemporalScope(str, Enum):
    """Temporal dimensionality of requested query."""
    MONO_TEMPORAL = "mono_temporal"  # 1 date
    BI_TEMPORAL = "bi_temporal"      # 2 dates (before vs after)
    MULTI_TEMPORAL = "multi_temporal"  # 3+ dates (trend/trajectory)


@dataclass
class MissionConstraints:
    """Scientific constraints that must be satisfied prior to mission execution."""
    requires_same_aoi: bool = True
    requires_coregistration: bool = False
    requires_sar_radar: bool = False
    requires_optical: bool = True
    min_spatial_overlap: float = 0.20
    max_cloud_cover: float = 0.60
    allow_cross_resolution: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requires_same_aoi": self.requires_same_aoi,
            "requires_coregistration": self.requires_coregistration,
            "requires_sar_radar": self.requires_sar_radar,
            "requires_optical": self.requires_optical,
            "min_spatial_overlap": self.min_spatial_overlap,
            "max_cloud_cover": self.max_cloud_cover,
            "allow_cross_resolution": self.allow_cross_resolution,
        }


@dataclass
class MissionSpec:
    """Complete structured specification of an Earth Observation query mission."""
    mission_id: str
    query: str
    intent: MissionIntent
    temporal_scope: TemporalScope
    target_phenomena: List[str]  # e.g., ["built_up", "water", "vegetation"]
    required_assets_count: int
    required_modalities: List[str]
    constraints: MissionConstraints
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    routing_score: float = 1.0
    routing_rationale: str = "Deterministic pattern match"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "query": self.query,
            "intent": self.intent.value,
            "temporal_scope": self.temporal_scope.value,
            "target_phenomena": self.target_phenomena,
            "required_assets_count": self.required_assets_count,
            "required_modalities": self.required_modalities,
            "constraints": self.constraints.to_dict(),
            "extracted_entities": self.extracted_entities,
            "routing_score": round(self.routing_score, 3),
            "routing_rationale": self.routing_rationale,
        }


class MissionParser:
    """Extracts MissionSpec from user query and available assets context."""

    # Keywords indicating spatial grounding
    GROUNDING_PATTERNS = [
        r"\blocat(e|ing|ion)\b", r"\bdetect\b", r"\bwhere is\b", r"\bwhere are\b",
        r"\bbounding box\b", r"\bbox\b", r"\bsegment\b", r"\bfind all\b",
        r"\bhighlight\b", r"\bpoint out\b",
    ]

    # Superlative ranking keywords
    SUPERLATIVE_PATTERNS = [
        r"\blargest\b", r"\bbiggest\b", r"\bmajor\b", r"\bmaximum\b",
        r"\bmost extensive\b", r"\bhighest area\b", r"\bsmallest\b",
        r"\btiniest\b", r"\bminimum\b", r"\blowest area\b",
    ]

    # Keywords indicating temporal change
    CHANGE_PATTERNS = [
        r"\bchang(e|ed|ing)\b", r"\bdiffer(ence|ent)\b", r"\bbefore and after\b",
        r"\bincreas(e|ed)\b", r"\bdecreas(e|ed)\b", r"\bexpand(ed|ing)?\b",
        r"\blos(s|t)\b", r"\bgrowth\b", r"\bencroach(ment)?\b", r"\bdemolish(ed)?\b",
        r"\bconstruct(ed|ion)\b", r"\burban sprawl\b", r"\bdeforestation\b",
    ]

    # Keywords indicating multi-modal SAR + Optical fusion
    FUSION_PATTERNS = [
        r"\bsar\b", r"\bradar\b", r"\bsentinel-1\b", r"\brisat\b",
        r"\bcorroborat(e|ion)\b", r"\bcross-modal\b", r"\bfus(e|ion)\b",
        r"\bcloud penetration\b", r"\bbackscatter\b", r"\bpolarimetr(ic|y)\b",
    ]

    # Target Earth phenomena patterns
    PHENOMENA_MAP = {
        "built_up": [r"\bbuilding(s)?\b", r"\burban\b", r"\broad(s)?\b", r"\bsettlement(s)?\b", r"\bconcrete\b", r"\bhous(e|es|ing)\b"],
        "water": [r"\bwater\b", r"\briver(s)?\b", r"\blake(s)?\b", r"\breservoir\b", r"\bflood(ing|ed)?\b", r"\binundat(ion|ed)\b"],
        "vegetation": [r"\bvegetation\b", r"\bforest(s)?\b", r"\btree(s)?\b", r"\bcrop(s)?\b", r"\bagricultur(e|al)\b", r"\bcanopy\b"],
        "cloud": [r"\bcloud(s)?\b", r"\bhaze\b", r"\bshadow(s)?\b"],
        "disaster": [r"\bdisaster\b", r"\bdamage\b", r"\blandslide\b", r"\bcyclone\b"],
    }

    def parse(
        self,
        query: str,
        available_assets_count: int = 1,
        has_sar_available: bool = False,
    ) -> MissionSpec:
        """Parse query string and context into a structured MissionSpec.
        
        Args:
            query: Natural language question or command.
            available_assets_count: Number of imagery assets provided.
            has_sar_available: Whether at least one SAR asset is in context.
            
        Returns:
            Structured MissionSpec.
        """
        q_lower = query.lower().strip()
        mission_id = f"msn_{uuid.uuid4().hex[:10]}"

        # 1. Detect phenomena
        detected_phenomena = []
        for phenom, patterns in self.PHENOMENA_MAP.items():
            if any(re.search(p, q_lower) for p in patterns):
                detected_phenomena.append(phenom)
        if not detected_phenomena:
            detected_phenomena = ["general_landcover"]

        # 2. Check keyword triggers
        has_grounding = any(re.search(p, q_lower) for p in self.GROUNDING_PATTERNS)
        has_change = any(re.search(p, q_lower) for p in self.CHANGE_PATTERNS)
        has_fusion = any(re.search(p, q_lower) for p in self.FUSION_PATTERNS) or (has_sar_available and "water" in detected_phenomena)

        has_ranking = any(re.search(p, q_lower) for p in self.SUPERLATIVE_PATTERNS) and any(p in detected_phenomena for p in ["water", "built_up", "vegetation"])

        # 3. Classify intent & temporal scope
        if has_change and has_fusion:
            intent = MissionIntent.COMPOUND_INVESTIGATION
            temporal = TemporalScope.BI_TEMPORAL
            req_assets = max(2, available_assets_count)
            req_mods = ["optical", "sar"]
            constraints = MissionConstraints(
                requires_same_aoi=True,
                requires_coregistration=True,
                requires_sar_radar=True,
                requires_optical=True,
            )
        elif has_fusion or (has_sar_available and "flood" in q_lower):
            intent = MissionIntent.CROSS_MODAL_FUSION
            temporal = TemporalScope.MONO_TEMPORAL
            req_assets = 2
            req_mods = ["optical", "sar"]
            constraints = MissionConstraints(
                requires_same_aoi=True,
                requires_coregistration=True,
                requires_sar_radar=True,
                requires_optical=True,
            )
        elif has_change or available_assets_count >= 2:
            intent = MissionIntent.TEMPORAL_CHANGE
            temporal = TemporalScope.BI_TEMPORAL if available_assets_count <= 2 else TemporalScope.MULTI_TEMPORAL
            req_assets = max(2, available_assets_count)
            req_mods = ["optical"]
            constraints = MissionConstraints(
                requires_same_aoi=True,
                requires_coregistration=True,
                requires_optical=True,
            )
        elif has_ranking:
            intent = MissionIntent.SPATIAL_RANKING
            temporal = TemporalScope.MONO_TEMPORAL
            req_assets = 1
            req_mods = ["optical"]
            constraints = MissionConstraints(
                requires_same_aoi=False,
                requires_coregistration=False,
                requires_optical=True,
            )
        elif has_grounding:
            intent = MissionIntent.VISUAL_GROUNDING
            temporal = TemporalScope.MONO_TEMPORAL
            req_assets = 1
            req_mods = ["optical"]
            constraints = MissionConstraints(
                requires_same_aoi=False,
                requires_coregistration=False,
                requires_optical=True,
            )
        else:
            intent = MissionIntent.SINGLE_IMAGE_VQA
            temporal = TemporalScope.MONO_TEMPORAL
            req_assets = 1
            req_mods = ["optical"]
            constraints = MissionConstraints(
                requires_same_aoi=False,
                requires_coregistration=False,
                requires_optical=True,
            )

        return MissionSpec(
            mission_id=mission_id,
            query=query,
            intent=intent,
            temporal_scope=temporal,
            target_phenomena=detected_phenomena,
            required_assets_count=req_assets,
            required_modalities=req_mods,
            constraints=constraints,
            extracted_entities={"phenomena": detected_phenomena},
            routing_score=1.0,
            routing_rationale=f"Query parsed to intent '{intent.value}' targeting '{','.join(detected_phenomena)}'",
        )
