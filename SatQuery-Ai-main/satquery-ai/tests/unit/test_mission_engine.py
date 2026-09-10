"""Unit tests for MissionParser, MissionPlanner, and MissionDAG."""

import pytest
from backend.mission import (
    MissionParser,
    MissionPlanner,
    MissionIntent,
    TemporalScope,
)


def test_mission_parser_intent_classification():
    parser = MissionParser()

    # VQA
    spec_vqa = parser.parse("What is the primary land cover in this scene?", available_assets_count=1)
    assert spec_vqa.intent == MissionIntent.SINGLE_IMAGE_VQA
    assert spec_vqa.temporal_scope == TemporalScope.MONO_TEMPORAL

    # Visual Grounding
    spec_ground = parser.parse("Locate the water reservoir and highlight its boundary.", available_assets_count=1)
    assert spec_ground.intent == MissionIntent.VISUAL_GROUNDING

    # Change Detection
    spec_change = parser.parse("Has the urban area expanded between before and after?", available_assets_count=2)
    assert spec_change.intent == MissionIntent.TEMPORAL_CHANGE
    assert spec_change.temporal_scope == TemporalScope.BI_TEMPORAL

    # Multimodal Corroboration
    spec_fusion = parser.parse("Corroborate flooded areas using Sentinel-1 radar backscatter.", available_assets_count=2, has_sar_available=True)
    assert spec_fusion.intent in [MissionIntent.CROSS_MODAL_FUSION, MissionIntent.COMPOUND_INVESTIGATION]


def test_mission_planner_dag_construction():
    parser = MissionParser()
    planner = MissionPlanner()

    spec = parser.parse("Has urban area increased between before and after images?", available_assets_count=2)
    dag = planner.plan(spec, ["img_before", "img_after"])

    assert len(dag.nodes) >= 5
    assert len(dag.execution_order) == len(dag.nodes)
    # Step 0 must be validation
    assert dag.execution_order[0] == "step_0_validate_assets"
    # Final step must be evidence synthesis
    assert dag.execution_order[-1] == "step_final_evidence_synthesis"
