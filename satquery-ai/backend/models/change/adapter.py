"""ModelAdapter implementation for Siamese Change Detection."""

from typing import Dict, Any, List, Optional
from pathlib import Path

from ..registry import ModelAdapter, model_registry
from .infer import ChangeDetector


class ChangeDetectorAdapter:
    """Model adapter wrapping the Siamese Change Detection model."""

    name: str = "siamese_change_detector"
    task: str = "bitemporal_change_detection"
    capabilities: List[str] = ["change_detection", "change_mask_generation", "change_quantification"]
    vram_estimate_mb: int = 800

    def __init__(self, checkpoint_path: Optional[Path | str] = None):
        self.checkpoint_path = checkpoint_path
        self._detector: Optional[ChangeDetector] = None
        self._status = "registered"

    @property
    def status(self) -> str:
        if self._detector is not None:
            return "ready"
        return self._status

    def load(self, device: str = "cpu") -> None:
        self._detector = ChangeDetector(checkpoint_path=self.checkpoint_path, device=device)
        self._status = "ready"

    def unload(self) -> None:
        self._detector = None
        self._status = "registered"

    def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task,
            "status": self.status,
            "is_loaded": self._detector is not None,
            "is_trained": self._detector.is_trained if self._detector else False,
            "vram_estimate_mb": self.vram_estimate_mb,
        }

    def detect(self, before_path: Path | str, after_path: Path | str, threshold: float = 0.5) -> Dict[str, Any]:
        if self._detector is None:
            self.load()
        assert self._detector is not None
        return self._detector.detect(before_path, after_path, threshold=threshold)


# Auto-register change detector in registry
change_detector_adapter = ChangeDetectorAdapter()
model_registry.register("change_detector", change_detector_adapter)
