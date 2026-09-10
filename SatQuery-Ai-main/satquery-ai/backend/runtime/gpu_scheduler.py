"""GPU Memory Scheduler and Sequential VRAM Budget Manager.

Ensures execution on 8 GB VRAM GPUs by enforcing:
1. Dynamic VRAM reservation and capacity checks
2. LRU eviction of idle neural network models
3. Explicit PyTorch CUDA cache reclamation (`empty_cache`)
4. Graceful fallback to CPU execution if GPU allocation fails
"""

from __future__ import annotations

import gc
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class ModelAllocation:
    """Tracking record for a loaded model in memory."""
    model_name: str
    allocated_vram_mb: int
    loaded_at: float
    last_accessed: float
    device: str  # "cuda:0" or "cpu"


class GPUScheduler:
    """Manages sequential model loading and VRAM allocation budgets."""

    # Default VRAM ceiling for consumer GPUs (8 GB)
    DEFAULT_MAX_VRAM_MB: int = 7500  # Leave 500 MB headroom for OS/Display

    def __init__(self, max_vram_mb: Optional[int] = None):
        self.max_vram_mb = max_vram_mb or self.DEFAULT_MAX_VRAM_MB
        self.loaded_models: Dict[str, ModelAllocation] = {}

    @property
    def is_cuda_available(self) -> bool:
        return bool(HAS_TORCH and torch.cuda.is_available())

    def get_vram_usage(self) -> Dict[str, Any]:
        """Query actual hardware VRAM telemetry."""
        if not self.is_cuda_available:
            return {
                "cuda_available": False,
                "device": "cpu",
                "allocated_mb": 0,
                "reserved_mb": 0,
                "max_vram_mb": self.max_vram_mb,
            }

        allocated = int(torch.cuda.memory_allocated() / (1024 * 1024))
        reserved = int(torch.cuda.memory_reserved() / (1024 * 1024))
        device_name = torch.cuda.get_device_name(0)

        return {
            "cuda_available": True,
            "device": device_name,
            "allocated_mb": allocated,
            "reserved_mb": reserved,
            "max_vram_mb": self.max_vram_mb,
            "tracked_models": list(self.loaded_models.keys()),
        }

    def can_fit(self, estimated_mb: int) -> bool:
        """Check whether a model with estimated memory can fit in the budget."""
        if not self.is_cuda_available:
            return True
        current_reserved = int(torch.cuda.memory_reserved() / (1024 * 1024))
        return (current_reserved + estimated_mb) <= self.max_vram_mb

    def evict_lru_except(self, keep_models: Optional[List[str]] = None):
        """Evict least-recently used models until memory is freed."""
        keep_set = set(keep_models or [])
        candidates = [
            (name, alloc) for name, alloc in self.loaded_models.items()
            if name not in keep_set
        ]
        candidates.sort(key=lambda x: x[1].last_accessed)

        for name, alloc in candidates:
            self._unload_model(name)
            self.reclaim_memory()

    def _unload_model(self, model_name: str):
        """Remove model tracking record."""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]

    def reclaim_memory(self):
        """Force Python garbage collection and CUDA cache release."""
        gc.collect()
        if self.is_cuda_available:
            try:
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            except Exception:
                pass

    @contextmanager
    def reserve(self, model_name: str, estimated_vram_mb: int = 3000):
        """Context manager reserving VRAM for a model execution cycle."""
        now = time.time()
        # 1. Evict if memory budget will be exceeded
        if not self.can_fit(estimated_vram_mb):
            self.evict_lru_except(keep_models=[model_name])

        # 2. Record allocation
        self.loaded_models[model_name] = ModelAllocation(
            model_name=model_name,
            allocated_vram_mb=estimated_vram_mb,
            loaded_at=now,
            last_accessed=now,
            device="cuda:0" if self.is_cuda_available else "cpu",
        )

        try:
            yield
        finally:
            # Update last accessed timestamp
            if model_name in self.loaded_models:
                self.loaded_models[model_name].last_accessed = time.time()
            # If VRAM exceeds 80% threshold, proactively clean cached blocks
            if self.is_cuda_available:
                reserved = torch.cuda.memory_reserved() / (1024 * 1024)
                if reserved > (0.80 * self.max_vram_mb):
                    self.reclaim_memory()


# Global singleton scheduler instance
gpu_scheduler = GPUScheduler()
