"""Autonomous Agent Orchestrator for multimodal remote sensing task dispatch."""

import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models_db import ImageRecord, AnalysisJob
from .router import classify_intent, IntentType
from .tool_registry import registry
from ..pipelines import (
    run_single_image_vqa_pipeline,
    run_visual_grounding_pipeline,
    run_bitemporal_change_pipeline,
    run_optical_sar_pipeline,
)


class AgentOrchestrator:
    """Orchestrates query understanding, input validation, workflow planning, and evidence grounding."""

    def dispatch_query(
        self,
        query: str,
        image_ids: List[str],
        db: Session,
        aoi_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch query across 3 validation layers (Intent, Input Validation, Workflow Planning)."""
        start_t = time.perf_counter()

        # Layer 2: Input Validation (Asset Existence)
        if not image_ids:
            raise ValueError("No images provided for analysis. Please upload or select an image asset.")

        images = [db.get(ImageRecord, img_id) for img_id in image_ids]
        valid_images = [img for img in images if img is not None]

        if not valid_images:
            raise ValueError("None of the specified image IDs exist in the database.")

        has_sar = any("sar" in (img.modality or "").lower() for img in valid_images)

        # Layer 1: Classify Task Intent
        intent, intent_conf, params = classify_intent(
            query=query,
            available_image_count=len(valid_images),
            has_sar=has_sar,
        )

        pipeline_result: Dict[str, Any] = {}
        synthesized_answer = ""

        # Layer 2: Modality & Spatial Input Checks
        if intent == IntentType.CHANGE_DETECTION:
            if len(valid_images) < 2:
                raise ValueError(
                    "Cannot perform temporal change analysis: exactly 2 corresponding observations (Before and After) are required, but only 1 was provided."
                )

        if intent == IntentType.OPTICAL_SAR_FUSION:
            if not has_sar and len(valid_images) < 2:
                raise ValueError(
                    "Optical + SAR multimodal corroboration requires both an Optical asset and a SAR radar asset."
                )

        # Layer 3: Multi-Step Workflow Planning & Tool Execution
        if intent == IntentType.GROUNDING:
            expr = params.get("referring_expression", query)
            pipeline_result = run_visual_grounding_pipeline(
                image_id=valid_images[0].id,
                referring_expression=expr,
                db=db,
            )
            count = len(pipeline_result.get("regions_geojson", {}).get("features", []))
            area_m2 = pipeline_result.get("total_area_m2", 0)
            area_ha = round(area_m2 / 10000.0, 4)
            synthesized_answer = (
                f"Located {count} spatial region(s) matching '{expr}' covering {area_m2:,.1f} m² ({area_ha} ha) in ground extent."
            )

        elif intent == IntentType.CHANGE_DETECTION:
            pipeline_result = run_bitemporal_change_pipeline(
                image_before_id=valid_images[1].id,
                image_after_id=valid_images[0].id,
                db=db,
                aoi_id=aoi_id,
            )
            pct = pipeline_result.get("change_percent", 0.0)
            area_m2 = pipeline_result.get("total_area_m2", 0.0)
            area_ha = pipeline_result.get("total_area_ha", 0.0)
            clusters = pipeline_result.get("cluster_count", 0)
            synthesized_answer = (
                f"Bi-temporal change analysis detected {pct}% surface alteration across {area_m2:,.1f} m² ({area_ha} ha) divided into {clusters} cluster(s)."
            )

        elif intent == IntentType.OPTICAL_SAR_FUSION:
            opt_img = next((img for img in valid_images if "sar" not in (img.modality or "").lower()), valid_images[0])
            sar_img = next((img for img in valid_images if "sar" in (img.modality or "").lower()), valid_images[-1])

            pipeline_result = run_optical_sar_pipeline(
                optical_image_id=opt_img.id,
                sar_image_id=sar_img.id,
                db=db,
                aoi_id=aoi_id,
            )
            synthesized_answer = pipeline_result.get("joint_claim", "Multimodal analysis completed.")

        else:  # IntentType.VQA or fallback
            pipeline_result = run_single_image_vqa_pipeline(
                image_id=valid_images[0].id,
                question=query,
                db=db,
            )
            synthesized_answer = pipeline_result.get("answer", "")

        job_id = pipeline_result.get("job_id", "")
        evidence = pipeline_result.get("evidence", {})
        confidence = pipeline_result.get("confidence", {})
        execution_steps = pipeline_result.get("execution_steps", [])

        # Standardized downloadable report links
        report_urls = {
            "pdf": f"/api/v1/reports/{job_id}/pdf",
            "geojson": f"/api/v1/reports/{job_id}/geojson",
            "csv": f"/api/v1/reports/{job_id}/csv",
        }

        return {
            "query": query,
            "intent": intent.value,
            "intent_confidence": intent_conf,
            "job_id": job_id,
            "answer": synthesized_answer,
            "pipeline_result": pipeline_result,
            "confidence": confidence,
            "evidence": evidence,
            "execution_steps": execution_steps,
            "report_urls": report_urls,
            "total_duration_ms": int((time.perf_counter() - start_t) * 1000),
        }


agent_orchestrator = AgentOrchestrator()
