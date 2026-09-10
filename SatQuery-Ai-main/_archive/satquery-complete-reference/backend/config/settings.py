"""
backend/config/settings.py

Single source of truth for hardware envelope, checkpoint paths, and the
real-vs-fallback feature flags that every specialist model and the agent
orchestrator read from. Centralising this stops "silent" fallback usage --
every EvidenceContract can trace back to exactly this config to explain
why fallback_used=True.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIR = REPO_ROOT / "checkpoints"
DATA_DEMO_DIR = REPO_ROOT / "data" / "demo"
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"
REPORTS_OUT_DIR = REPO_ROOT / "outputs" / "reports"

for _d in (CHECKPOINT_DIR, DATA_DEMO_DIR, RESULTS_DIR, REPORTS_OUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _env_bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class HardwareEnvelope:
    """Matches the README's stated envelope: single 8GB RTX 4060."""
    total_vram_gb: float = 8.0
    geochat_vram_budget_gb: float = 4.5
    changenet_vram_budget_gb: float = 1.5
    dofa_vram_budget_gb: float = 1.5
    headroom_gb: float = 0.5


@dataclass
class ModelPaths:
    geochat: Path = CHECKPOINT_DIR / "geochat-7b"
    changenet: Path = CHECKPOINT_DIR / "changenet"
    dofa: Path = CHECKPOINT_DIR / "dofa-vitb"


@dataclass
class FeatureFlags:
    """
    Each flag independently controls whether the corresponding pipeline
    attempts the real model first. If the checkpoint is missing or the
    model errors at load/infer time, the pipeline degrades to its
    deterministic fallback and stamps fallback_used=True on the evidence
    -- it never silently pretends the real model ran.
    """
    allow_geochat_fallback: bool = field(
        default_factory=lambda: _env_bool("SATQUERY_ALLOW_GEOCHAT_FALLBACK", True)
    )
    allow_changenet_fallback: bool = field(
        default_factory=lambda: _env_bool("SATQUERY_ALLOW_CHANGENET_FALLBACK", True)
    )
    allow_dofa_fallback: bool = field(
        default_factory=lambda: _env_bool("SATQUERY_ALLOW_DOFA_FALLBACK", True)
    )
    force_fallback_only: bool = field(
        default_factory=lambda: _env_bool("SATQUERY_FORCE_FALLBACK_ONLY", False)
    )


HARDWARE = HardwareEnvelope()
PATHS = ModelPaths()
FLAGS = FeatureFlags()

# Default CRS assumptions when a raster has no CRS tag (demo/synthetic data).
DEFAULT_GEOGRAPHIC_CRS = "EPSG:4326"
