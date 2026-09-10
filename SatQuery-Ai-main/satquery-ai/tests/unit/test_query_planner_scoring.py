"""Unit tests verifying QueryCapabilityPlanner and MissionSpec routing score decoupling."""

import pytest
from backend.agent.query_planner import query_capability_planner, QueryPlan
from backend.mission.parser import MissionParser, MissionSpec, MissionIntent


class TestQueryPlannerScoringDecoupling:

    def test_query_plan_uses_routing_score_not_confidence(self):
        """Verify that QueryPlan exposes routing_score and routing_reason instead of synthetic confidence."""
        plan = query_capability_planner.plan("Where is the largest water body?")
        assert isinstance(plan, QueryPlan)
        assert plan.intent == "spatial_ranking"
        assert plan.target == "water_body"
        assert plan.operation == "largest"

        # Check fields
        assert hasattr(plan, "routing_score")
        assert hasattr(plan, "routing_reason")
        assert hasattr(plan, "matched_patterns")
        assert not hasattr(plan, "confidence")

        d = plan.to_dict()
        assert "routing_score" in d
        assert "routing_reason" in d
        assert "matched_patterns" in d
        assert "confidence" not in d
        assert d["routing_score"] == 1.0

    def test_mission_spec_uses_routing_score_not_confidence(self):
        """Verify that MissionSpec has routing_score and routing_rationale instead of synthetic confidence."""
        parser = MissionParser()
        spec = parser.parse("Detect change between 2024 and 2026")
        assert isinstance(spec, MissionSpec)
        assert spec.intent == MissionIntent.TEMPORAL_CHANGE

        assert hasattr(spec, "routing_score")
        assert hasattr(spec, "routing_rationale")
        assert not hasattr(spec, "confidence")

        d = spec.to_dict()
        assert "routing_score" in d
        assert "routing_rationale" in d
        assert "confidence" not in d
        assert d["routing_score"] == 1.0

    def test_zero_heuristic_confidence_in_all_planner_branches(self):
        """Verify that all planner branches produce routing_score, not synthetic 0.96/0.92/0.88."""
        queries = [
            "Where is the largest water body?",
            "Identify built-up change with SAR",
            "Radar water backscatter",
            "Locate runway",
            "Describe the overall scene",
        ]

        for q in queries:
            plan = query_capability_planner.plan(q)
            assert plan.routing_score == 1.0
            assert len(plan.routing_reason) > 0
            assert "confidence" not in plan.to_dict()
