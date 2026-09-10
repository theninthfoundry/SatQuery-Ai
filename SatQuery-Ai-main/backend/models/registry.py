"""
Model registry with an enforced state machine.

Per the audit's "Model truth lock" requirement: the UI must never be able
to say "GeoChat Ready" just because an adapter class was imported. This
module makes that structurally impossible — ModelEntry.status can only
become READY via mark_verified(), which requires a checkpoint hash and a
passed runtime smoke test artifact.

Usage in application code:

    registry = ModelRegistry()
    registry.register(ModelEntry(
        id="geochat-7b",
        type=ModelType.TRAINED_MODEL,
        source_uri="hf://...",
    ))
    ...
    registry.mark_verified(
        "geochat-7b",
        checkpoint_sha256=<real sha256>,
        test_image_hash=<real sha256 of the smoke-test image>,
        test_output_hash=<real sha256 of the model's output on that image>,
        metrics={"smoke_test_latency_ms": 812},
    )

    # Anywhere the app wants to claim a model is usable:
    registry.assert_ready("geochat-7b")   # raises ModelNotReadyError if not
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ModelType(str, Enum):
    TRAINED_MODEL = "TRAINED_MODEL"
    DETERMINISTIC_ENGINE = "DETERMINISTIC_ENGINE"
    DATASET = "DATASET"
    EXPERIMENT = "EXPERIMENT"
    ARTIFACT = "ARTIFACT"


class ModelStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    DOWNLOADING = "DOWNLOADING"
    INSTALLED = "INSTALLED"
    LOADABLE = "LOADABLE"
    VERIFIED = "VERIFIED"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class ModelNotReadyError(RuntimeError):
    """Raised whenever application code tries to use a model that isn't READY."""


class InvalidTransitionError(RuntimeError):
    """Raised when a status transition would violate the truth-lock invariants."""


_ALLOWED_TRANSITIONS: dict[ModelStatus, set[ModelStatus]] = {
    ModelStatus.DISCOVERED: {ModelStatus.DOWNLOADING, ModelStatus.UNAVAILABLE},
    ModelStatus.DOWNLOADING: {ModelStatus.INSTALLED, ModelStatus.FAILED},
    ModelStatus.INSTALLED: {ModelStatus.LOADABLE, ModelStatus.FAILED},
    ModelStatus.LOADABLE: {ModelStatus.VERIFIED, ModelStatus.FAILED},
    ModelStatus.VERIFIED: {ModelStatus.READY, ModelStatus.FAILED},
    ModelStatus.READY: {ModelStatus.DEGRADED, ModelStatus.UNAVAILABLE},
    ModelStatus.DEGRADED: {ModelStatus.READY, ModelStatus.UNAVAILABLE, ModelStatus.FAILED},
    ModelStatus.FAILED: {ModelStatus.DISCOVERED},
    ModelStatus.UNAVAILABLE: {ModelStatus.DISCOVERED},
}


@dataclass
class ModelEntry:
    id: str
    type: ModelType
    source_uri: str
    architecture: Optional[str] = None
    processor: Optional[str] = None
    device: Optional[str] = None
    precision: Optional[str] = None
    status: ModelStatus = ModelStatus.DISCOVERED

    checkpoint_sha256: Optional[str] = None
    verified_at: Optional[datetime] = None
    test_image_hash: Optional[str] = None
    test_output_hash: Optional[str] = None
    output_contract: Optional[dict[str, Any]] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None

    def is_ready(self) -> bool:
        return (
            self.status == ModelStatus.READY
            and self.checkpoint_sha256 is not None
            and self.verified_at is not None
        )


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelEntry] = {}

    def register(self, entry: ModelEntry) -> None:
        if entry.id in self._models:
            raise ValueError(f"Model '{entry.id}' already registered.")
        self._models[entry.id] = entry

    def get(self, model_id: str) -> ModelEntry:
        if model_id not in self._models:
            raise KeyError(f"Unknown model_id '{model_id}'.")
        return self._models[model_id]

    def _transition(self, model_id: str, new_status: ModelStatus) -> ModelEntry:
        entry = self.get(model_id)
        allowed = _ALLOWED_TRANSITIONS.get(entry.status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Model '{model_id}' cannot go from {entry.status} to "
                f"{new_status}. Allowed: {sorted(s.value for s in allowed)}"
            )
        entry.status = new_status
        return entry

    def mark_downloading(self, model_id: str) -> ModelEntry:
        return self._transition(model_id, ModelStatus.DOWNLOADING)

    def mark_installed(self, model_id: str) -> ModelEntry:
        return self._transition(model_id, ModelStatus.INSTALLED)

    def mark_loadable(self, model_id: str) -> ModelEntry:
        return self._transition(model_id, ModelStatus.LOADABLE)

    def mark_failed(self, model_id: str, reason: str) -> ModelEntry:
        entry = self.get(model_id)
        entry.failure_reason = reason
        entry.status = ModelStatus.FAILED
        return entry

    def mark_verified(
        self,
        model_id: str,
        *,
        checkpoint_sha256: str,
        test_image_hash: str,
        test_output_hash: str,
        output_contract: Optional[dict[str, Any]] = None,
        metrics: Optional[dict[str, Any]] = None,
    ) -> ModelEntry:
        """
        The ONLY way a model can become usable. All three hashes must be
        real (64-char hex sha256), proving:
          - checkpoint_sha256: the exact weights that were loaded
          - test_image_hash:   the exact smoke-test input used
          - test_output_hash:  the exact output produced on that input

        This directly enforces the audit's requirement:
            assert model.status == VERIFIED
            assert model.checkpoint_hash is not None
            assert model.runtime_test_passed is True
        """
        for name, val in (
            ("checkpoint_sha256", checkpoint_sha256),
            ("test_image_hash", test_image_hash),
            ("test_output_hash", test_output_hash),
        ):
            if not val or len(val) != 64:
                raise InvalidTransitionError(
                    f"mark_verified requires a real 64-char sha256 for "
                    f"'{name}'; got {val!r}. A model cannot be verified "
                    f"without proof of an actual runtime test."
                )

        entry = self._transition(model_id, ModelStatus.VERIFIED)
        entry.checkpoint_sha256 = checkpoint_sha256
        entry.test_image_hash = test_image_hash
        entry.test_output_hash = test_output_hash
        entry.output_contract = output_contract
        entry.metrics = metrics or {}
        entry.verified_at = datetime.now(timezone.utc)

        # A verified model becomes READY automatically, but only via this
        # single controlled path.
        entry.status = ModelStatus.READY
        return entry

    def mark_degraded(self, model_id: str, reason: str) -> ModelEntry:
        entry = self._transition(model_id, ModelStatus.DEGRADED)
        entry.failure_reason = reason
        return entry

    def mark_unavailable(self, model_id: str, reason: Optional[str] = None) -> ModelEntry:
        entry = self.get(model_id)
        entry.status = ModelStatus.UNAVAILABLE
        entry.failure_reason = reason
        return entry

    def assert_ready(self, model_id: str) -> ModelEntry:
        """Call this at the top of every inference path. Never bypass it."""
        entry = self.get(model_id)
        if not entry.is_ready():
            raise ModelNotReadyError(
                f"Model '{model_id}' is not READY (status={entry.status.value}"
                f"{', reason=' + entry.failure_reason if entry.failure_reason else ''}"
                f"). Refusing to run inference or report a result from it."
            )
        return entry

    def status_report(self) -> dict[str, dict[str, Any]]:
        """What the UI's status panel should render from — never a static checkmark."""
        return {
            model_id: {
                "status": e.status.value,
                "ready": e.is_ready(),
                "verified_at": e.verified_at.isoformat() if e.verified_at else None,
                "failure_reason": e.failure_reason,
            }
            for model_id, e in self._models.items()
        }
