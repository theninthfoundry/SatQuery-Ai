"""Unit tests for the 3-Layer Agent Validation and Tool Registry."""

import pytest
from pathlib import Path
from backend.agent.router import classify_intent, IntentType
from backend.agent.tool_registry import registry
from backend.agent.orchestrator import agent_orchestrator
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord


def test_layer1_intent_classification():
    intent1, _, _ = classify_intent("Describe land cover types")
    assert intent1 == IntentType.VQA

    intent2, _, _ = classify_intent("Highlight the airport runway")
    assert intent2 == IntentType.GROUNDING

    intent3, _, _ = classify_intent("What changed between these observations?", available_image_count=2)
    assert intent3 == IntentType.CHANGE_DETECTION

    intent4, _, _ = classify_intent("Corroborate with SAR backscatter")
    assert intent4 == IntentType.OPTICAL_SAR_FUSION


def test_layer2_input_validation_rejections():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())

    # 1. Change detection with only 1 image must be rejected
    dummy_img = db.get(ImageRecord, "img_demo_optical_1")
    if not dummy_img:
        dummy_img = ImageRecord(
            id="img_demo_optical_1",
            filename="scene.tif",
            path="data/demo/scene_optical_ahmedabad.tif",
            format="GTiff",
            width=128,
            height=128,
            band_count=4,
            is_valid=True,
        )
        db.merge(dummy_img)
        db.commit()

    with pytest.raises(ValueError, match="Cannot perform temporal change analysis"):
        agent_orchestrator.dispatch_query(
            query="What changed between these observations?",
            image_ids=["img_demo_optical_1"],  # only 1 image
            db=db,
        )


def test_layer3_tool_registry_scientific_capabilities():
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    assert "single_image_vqa_tool" in tool_names
    assert "visual_grounding_tool" in tool_names
    assert "change_detection_tool" in tool_names
    assert "optical_sar_corroboration_tool" in tool_names
    assert "geometry_polygonize_and_measure_tool" in tool_names
