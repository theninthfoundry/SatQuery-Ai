"""Unit tests for the Unified LLM Synthesis Client."""

import pytest
from backend.agent.llm_client import UnifiedLLMClient, llm_client


def test_local_offline_synthesis_fallback():
    client = UnifiedLLMClient()
    default_text = "Detected 12.5% surface alteration across 25,600.0 m² (2.56 ha)."

    res = client.synthesize(
        query="What changed between these dates?",
        task_intent="change_detection",
        pipeline_result={"change_percent": 12.5, "total_area_m2": 25600.0},
        default_answer=default_text,
    )

    assert res == default_text


def test_llm_client_instance_exists():
    assert llm_client is not None
    assert hasattr(llm_client, "synthesize")
