"""Autonomous Agent Orchestrator for multimodal remote sensing task dispatch.

Powered by the Mission Engine:
1. Natural language query → MissionSpec via MissionParser
2. MissionSpec → Execution DAG via MissionPlanner
3. Execution DAG → Telemetry & Provenance via MissionExecutor
4. Evidence Synthesis & Calibrated Confidence via EvidenceGate
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models_db import ImageRecord, AnalysisJob
from .router import classify_intent, IntentType
from .tool_registry import registry
from .llm_client import llm_client
from ..mission import (
    MissionParser,
    MissionPlanner,
    MissionExecutor,
    MissionSpec,
    MissionDAG,
)
from ..evidence import compute_multimodal_confidence, build_evidence, ExecutionStep


class AgentOrchestrator:
    """Orchestrates query understanding, mission planning, DAG execution, and evidence grounding."""

    def __init__(self):
        self.parser = MissionParser()
        self.planner = MissionPlanner()
        self.executor = MissionExecutor()

    def dispatch_query(
        self,
        query: str,
        image_ids: List[str],
        db: Session,
        aoi_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch query across the Mission Engine: Parse → Plan DAG → Execute → Ground."""
        start_t = time.perf_counter()

        # 1. Asset Existence & Validation
        if not image_ids:
            raise ValueError("No images provided for analysis. Please upload or select an image asset.")

        images = [db.get(ImageRecord, img_id) for img_id in image_ids]
        valid_images = [img for img in images if img is not None]

        if not valid_images:
            raise ValueError("None of the specified image IDs exist in the database.")

        has_sar = any("sar" in (img.modality or "").lower() for img in valid_images)

        # 2. Parse Mission Specification
        spec = self.parser.parse(
            query=query,
            available_assets_count=len(valid_images),
            has_sar_available=has_sar,
        )

        # 3. Scientific Pre-flight Validation Constraints
        if spec.intent.value in ["temporal_change", "compound_investigation"] and len(valid_images) < 2:
            raise ValueError(
                "Cannot perform temporal change analysis: exactly 2 corresponding observations (Before and After) are required, but only 1 was provided."
            )

        if spec.intent.value == "cross_modal_fusion" and not has_sar and len(valid_images) < 2:
            raise ValueError(
                "Optical + SAR multimodal corroboration requires both an Optical asset and a SAR radar asset."
            )

        # For mono-temporal single-scene analysis, align target asset semantically if general list was passed
        if spec.intent.value in ["spatial_ranking", "single_image_vqa", "visual_grounding"] and len(valid_images) > 1:
            if "water" in spec.target_phenomena:
                water_matches = [img for img in valid_images if any(k in img.id.lower() or k in (img.filename or "").lower() for k in ["water", "flood", "lake", "river", "brahmaputra"])]
                if water_matches:
                    other_imgs = [img for img in valid_images if img.id not in [w.id for w in water_matches]]
                    valid_images = water_matches + other_imgs

        # 4. Generate Mission DAG
        dag = self.planner.plan(spec, [img.id for img in valid_images])

        # 5. Execute Mission DAG
        mission_report = self.executor.execute(dag, db=db, query=query, aoi_id=aoi_id)

        # 6. Extract pipeline result, job_id, and execution steps
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        evidence = mission_report.evidence_artifacts
        confidence = {
            "overall": mission_report.confidence,
            "calibrated": mission_report.confidence,
            "components": mission_report.confidence_breakdown,
        }

        # Convert mission telemetry to ExecutionStep list for backward-compatible UI
        execution_steps = [
            {
                "step_name": s.name,
                "tool": s.tool_or_model,
                "status": s.status,
                "duration_ms": int(s.duration_sec * 1000),
                "summary": s.output_summary,
            }
            for s in mission_report.steps_telemetry
        ]

        # Grounded synthesis via LLM or rule synthesizer
        final_answer = llm_client.synthesize(
            query=query,
            task_intent=spec.intent.value,
            pipeline_result=evidence,
            default_answer=mission_report.synthesized_answer,
        )

        # Record job in database
        try:
            db_job = AnalysisJob(
                id=job_id,
                aoi_id=aoi_id,
                query=query,
                task=spec.intent.value,
                status="COMPLETED",
                result_json={
                    "answer": final_answer,
                    "mission_id": spec.mission_id,
                    "confidence": confidence,
                    "timeline": [s.to_dict() for s in mission_report.steps_telemetry],
                },
                confidence_json=confidence,
                execution_time_ms=int((time.perf_counter() - start_t) * 1000),
            )
            db.add(db_job)
            db.commit()
        except Exception:
            pass  # Non-fatal if DB transaction fails

        # Standardized downloadable report links
        report_urls = {
            "pdf": f"/api/v1/reports/{job_id}/pdf",
            "geojson": f"/api/v1/reports/{job_id}/geojson",
            "csv": f"/api/v1/reports/{job_id}/csv",
        }

        return {
            "query": query,
            "intent": spec.intent.value,
            "routing_score": spec.routing_score,
            "job_id": job_id,
            "mission_id": spec.mission_id,
            "answer": final_answer,
            "pipeline_result": evidence,
            "confidence": confidence,
            "evidence": evidence,
            "execution_steps": execution_steps,
            "mission_dag": dag.to_dict(),
            "report_urls": report_urls,
            "warnings": mission_report.warnings,
            "total_duration_ms": int((time.perf_counter() - start_t) * 1000),
        }


agent_orchestrator = AgentOrchestrator()
