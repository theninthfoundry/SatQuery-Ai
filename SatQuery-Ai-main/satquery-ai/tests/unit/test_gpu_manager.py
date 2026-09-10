"""Unit tests for GPUManager and sequential execution."""

import pytest
from backend.models.manager import GPUManager
from backend.models.registry import ModelRegistry
from backend.models.change.adapter import ChangeDetectorAdapter


def test_gpu_manager_device_discovery():
    manager = GPUManager()
    status = manager.get_hardware_status()
    assert "torch_available" in status
    assert "cuda_available" in status
    assert status["device"] in ("cpu", "cuda:0")


def test_gpu_manager_sequential_lifecycle():
    registry = ModelRegistry()
    change_adapter = ChangeDetectorAdapter()
    registry.register("change_detector", change_adapter)

    manager = GPUManager(registry=registry)

    # Initial state
    assert manager.active_model is None

    # Load model
    loaded = manager.load_model("change_detector", target_device="cpu")
    assert loaded is not None
    assert manager.active_model_name == "change_detector"
    assert manager.active_model.status == "ready"

    # Metrics tracked
    assert manager.last_metrics is not None
    assert manager.last_metrics.model_name == "change_detector"

    # Unload
    manager.unload_active()
    assert manager.active_model is None
    assert manager.active_model_name is None
