"""Unit tests for Model Registry and Adapter Protocol."""

import pytest
from backend.models.registry import ModelRegistry, StubModelAdapter
from backend.models.change.adapter import ChangeDetectorAdapter


def test_model_registry_registration():
    registry = ModelRegistry()

    # Check default stub models
    geochat = registry.get("geochat")
    assert geochat is not None
    assert geochat.status == "not_installed"
    assert "vqa" in geochat.capabilities

    # Check change detector
    change_adapter = ChangeDetectorAdapter()
    registry.register("test_change", change_adapter)
    assert registry.get("test_change") is not None
    assert registry.get("test_change").status == "registered"


def test_stub_model_load_raises():
    stub = StubModelAdapter(
        name="TestVLM",
        task="vqa",
        description="Test",
        capabilities=["vqa"],
        vram_estimate_mb=4000,
        phase_target="Phase 1",
    )
    assert stub.status == "not_installed"
    with pytest.raises(NotImplementedError, match="scheduled for Phase 1"):
        stub.load()


def test_model_registry_list_models():
    registry = ModelRegistry()
    models = registry.list_models()
    assert len(models) >= 2
    keys = [m["key"] for m in models]
    assert "geochat" in keys
    assert "dofa" in keys
