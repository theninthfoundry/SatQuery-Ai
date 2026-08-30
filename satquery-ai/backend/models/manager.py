"""GPU Runtime and sequential model lifecycle manager."""

import os
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..config import settings
from .registry import ModelRegistry, ModelAdapter, model_registry

try:
    import torch
    HAS_TORCH = True
except ImportError:  # pragma: no cover
    HAS_TORCH = False


@dataclass
class ExecutionMetrics:
    model_name: str
    device: str
    load_time_sec: float
    vram_before_mb: float
    vram_after_mb: float
    peak_vram_mb: float


class GPUManager:
    """Manages sequential model residence in GPU memory under strict VRAM constraints."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or model_registry
        self.active_model: Optional[ModelAdapter] = None
        self.active_model_name: Optional[str] = None
        self.last_metrics: Optional[ExecutionMetrics] = None

    @property
    def is_cuda_available(self) -> bool:
        if not HAS_TORCH or settings.force_cpu:
            return False
        return torch.cuda.is_available()

    @property
    def primary_device(self) -> str:
        if self.is_cuda_available:
            return "cuda:0"
        return "cpu"

    def get_vram_usage(self) -> Tuple[float, float, float]:
        """Return (allocated_mb, reserved_mb, max_allocated_mb) from PyTorch CUDA."""
        if not self.is_cuda_available:
            return 0.0, 0.0, 0.0
        allocated = torch.cuda.memory_allocated() / (1024 * 1024)
        reserved = torch.cuda.memory_reserved() / (1024 * 1024)
        max_alloc = torch.cuda.max_memory_allocated() / (1024 * 1024)
        return round(allocated, 2), round(reserved, 2), round(max_alloc, 2)

    def get_hardware_status(self) -> Dict[str, Any]:
        """Return current GPU and system memory diagnostics."""
        status: Dict[str, Any] = {
            "torch_available": HAS_TORCH,
            "cuda_available": self.is_cuda_available,
            "device": self.primary_device,
            "active_model": self.active_model_name,
        }

        if self.is_cuda_available:
            props = torch.cuda.get_device_properties(0)
            total_mb = props.total_memory / (1024 * 1024)
            alloc_mb, res_mb, peak_mb = self.get_vram_usage()
            status["gpu"] = {
                "name": props.name,
                "total_vram_mb": round(total_mb, 2),
                "allocated_vram_mb": alloc_mb,
                "reserved_vram_mb": res_mb,
                "peak_vram_mb": peak_mb,
                "multi_processor_count": props.multi_processor_count,
            }
        else:
            status["gpu"] = None

        return status

    def unload_active(self) -> None:
        """Evict currently resident model from memory and flush CUDA cache."""
        if self.active_model is not None:
            self.active_model.unload()
            self.active_model = None
            self.active_model_name = None

        if self.is_cuda_available:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

    def load_model(self, key: str, target_device: Optional[str] = None) -> ModelAdapter:
        """Sequentially load requested model, evicting any previously active model."""
        device = target_device or self.primary_device
        adapter = self.registry.get(key)

        if adapter is None:
            raise KeyError(f"Model '{key}' is not registered in ModelRegistry")

        # If already loaded and active, return directly
        if self.active_model_name == key and adapter.status == "ready":
            return adapter

        # Evict prior model first to guarantee sequential VRAM usage
        self.unload_active()

        vram_before, _, _ = self.get_vram_usage()
        start_t = time.perf_counter()

        adapter.load(device=device)

        load_t = time.perf_counter() - start_t
        vram_after, _, peak_vram = self.get_vram_usage()

        self.active_model = adapter
        self.active_model_name = key
        self.last_metrics = ExecutionMetrics(
            model_name=key,
            device=device,
            load_time_sec=round(load_t, 4),
            vram_before_mb=vram_before,
            vram_after_mb=vram_after,
            peak_vram_mb=peak_vram,
        )

        return adapter


gpu_manager = GPUManager()
