"""Model registry and adapter interfaces for remote sensing AI models."""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from dataclasses import dataclass, field


@runtime_checkable
class ModelAdapter(Protocol):
    """Standardized interface for all perception and VLM model adapters."""
    name: str
    task: str
    capabilities: List[str]
    vram_estimate_mb: int

    @property
    def status(self) -> str:
        """Return 'registered', 'not_installed', 'ready', or 'error'."""
        ...

    def load(self, device: str = "cpu") -> None:
        """Load model weights onto target device."""
        ...

    def unload(self) -> None:
        """Evict model from device memory."""
        ...

    def health(self) -> Dict[str, Any]:
        """Return diagnostic health and availability status."""
        ...


@dataclass
class ModelMetadata:
    name: str
    task: str
    description: str
    capabilities: List[str]
    vram_estimate_mb: int
    status: str  # "registered", "not_installed", "ready", "error"
    notes: str = ""


class StubModelAdapter:
    """Explicit uninstalled / Phase-1 candidate model adapter."""

    def __init__(
        self,
        name: str,
        task: str,
        description: str,
        capabilities: List[str],
        vram_estimate_mb: int,
        phase_target: str = "Phase 1",
    ):
        self.name = name
        self.task = task
        self.description = description
        self.capabilities = capabilities
        self.vram_estimate_mb = vram_estimate_mb
        self.phase_target = phase_target
        self._is_loaded = False

    @property
    def status(self) -> str:
        return "not_installed"

    def load(self, device: str = "cpu") -> None:
        raise NotImplementedError(
            f"Model '{self.name}' is scheduled for {self.phase_target} and is not yet installed in Phase 0."
        )

    def unload(self) -> None:
        self._is_loaded = False

    def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task,
            "status": self.status,
            "installed": False,
            "vram_estimate_mb": self.vram_estimate_mb,
            "message": f"Model '{self.name}' not installed. Scheduled for {self.phase_target}.",
        }


class ModelRegistry:
    """Central registry tracking all AI model adapters and metadata."""

    def __init__(self):
        self._models: Dict[str, ModelAdapter] = {}
        self._register_default_models()

    def _register_default_models(self) -> None:
        # Register planned foundation & perception models with honest 'not_installed' status
        self.register(
            "geochat",
            StubModelAdapter(
                name="GeoChat-7B",
                task="vqa_and_grounding",
                description="Remote sensing vision-language model for single-image VQA and visual grounding",
                capabilities=["vqa", "grounding", "scene_description"],
                vram_estimate_mb=4500,
                phase_target="Phase 1",
            ),
        )
        self.register(
            "dofa",
            StubModelAdapter(
                name="DOFA-Foundation",
                task="cross_modal_representation",
                description="Dynamic Optical-SAR Foundation model for multi-sensor embedding",
                capabilities=["optical_feature_extraction", "sar_feature_extraction"],
                vram_estimate_mb=2500,
                phase_target="Phase 1",
            ),
        )

    def register(self, key: str, adapter: ModelAdapter) -> None:
        self._models[key] = adapter

    def get(self, key: str) -> Optional[ModelAdapter]:
        return self._models.get(key)

    def list_models(self) -> List[Dict[str, Any]]:
        result = []
        for key, m in self._models.items():
            result.append({
                "key": key,
                "name": getattr(m, "name", key),
                "task": getattr(m, "task", "unknown"),
                "status": m.status,
                "capabilities": getattr(m, "capabilities", []),
                "vram_estimate_mb": getattr(m, "vram_estimate_mb", 0),
            })
        return result


model_registry = ModelRegistry()
