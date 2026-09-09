"""
backend/agent/orchestrator.py

The single entrypoint everything else (API, CLI, tests) calls. Ties
together: Layer 1/2 routing -> Layer 3 tool dispatch -> pipelines ->
evidence. This is the "autonomous agent orchestrator" from the README.

Usage:
    from backend.agent.orchestrator import SatQueryAgent
    agent = SatQueryAgent()
    result = agent.handle_query(
        query="Has built-up area increased, where did it occur?",
        image_paths=["data/demo/urban_t1.tif", "data/demo/urban_t2.tif"],
        image_modalities=["optical", "optical"],
    )
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from backend.agent.router import route, RoutingDecision
from backend.agent.tool_registry import TaskType
from backend.geospatial import engine as geo
from backend.pipelines import pipelines as pl


class RoutingError(RuntimeError):
    """Raised when Layer 1/2 rejects a request -- carries the routing
    decision so the API layer can return a structured 4xx with reasons
    instead of a generic 500."""

    def __init__(self, decision: RoutingDecision):
        self.decision = decision
        reasons = "; ".join(decision.validation.reasons) or "unspecified validation failure"
        super().__init__(f"Cannot execute task '{decision.task.value}': {reasons}")


@dataclass
class AgentResponse:
    task: str
    routing_summary: dict
    evidence: dict
    total_latency_ms: float


class SatQueryAgent:
    """Stateless orchestrator -- safe to instantiate per-request. Model
    lifecycle (load/unload) is owned by each pipeline function, which is
    what keeps VRAM usage sequential rather than accumulating models
    across requests (see geochat adapter docstring)."""

    def handle_query(self, query: str, image_paths: list,
                      image_modalities: Optional[list] = None,
                      threshold: Optional[float] = None) -> AgentResponse:
        t0 = time.perf_counter()

        rasters = [geo.read_raster_info(p) for p in image_paths]
        decision = route(query, rasters)

        if not decision.can_execute:
            raise RoutingError(decision)

        task = decision.task
        ref_expr = decision.intent.referring_expression

        if task == TaskType.VQA:
            evidence = pl.run_vqa(image_paths[0], query)
        elif task == TaskType.CAPTIONING:
            evidence = pl.run_captioning(image_paths[0])
        elif task == TaskType.GROUNDING:
            evidence = pl.run_grounding(image_paths[0], ref_expr or query)
        elif task in (TaskType.CHANGE_DETECTION, TaskType.CHANGE_VQA):
            evidence = pl.run_change_detection(image_paths[0], image_paths[1], query=query,
                                                threshold=threshold)
        elif task == TaskType.FUSION_OPTICAL_SAR:
            opt_idx, sar_idx = self._resolve_optical_sar_indices(image_modalities)
            evidence = pl.run_fusion_optical_sar(image_paths[opt_idx], image_paths[sar_idx], query=query)
        elif task == TaskType.GOLDEN_MISSION:
            evidence = pl.run_golden_mission_urban_expansion(image_paths[0], image_paths[1], query)
        else:
            raise ValueError(f"No pipeline wired for task {task}")

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return AgentResponse(
            task=task.value,
            routing_summary={
                "matched_pattern": decision.intent.matched_pattern,
                "referring_expression": ref_expr,
                "tool_selected": decision.validation.tool.name,
                "validation_reasons": decision.validation.reasons,
                "overlap_fraction": (decision.validation.pair_check.overlap_fraction
                                      if decision.validation.pair_check else None),
            },
            evidence=evidence,
            total_latency_ms=round(latency_ms, 2),
        )

    @staticmethod
    def _resolve_optical_sar_indices(modalities: Optional[list]) -> tuple:
        if not modalities or len(modalities) != 2:
            raise ValueError(
                "Optical+SAR fusion requires image_modalities=['optical','sar'] "
                "(or reversed) to disambiguate which upload is which."
            )
        mlow = [m.lower() for m in modalities]
        if "sar" not in mlow or "optical" not in mlow:
            raise ValueError(f"image_modalities must contain 'optical' and 'sar', got {modalities}")
        return mlow.index("optical"), mlow.index("sar")
