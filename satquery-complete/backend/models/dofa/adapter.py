"""
backend/models/dofa/adapter.py

Optical + SAR cross-modal corroboration. DOFA (Dynamic One-For-All) is a
wavelength-conditioned ViT that natively ingests arbitrary spectral bands
(optical multispectral AND SAR) through one backbone -- real path below.

The fallback path is *not* a neural network; it is domain-standard remote
sensing index math:
  - NDWI (water) and NDBI (built-up) from optical bands
  - SAR backscatter thresholding (sigma-nought < -20dB => likely water /
    specular surface; consistently high => built-up/urban corner
    reflectors)
  - A cross-modal agreement map: pixels where optical and SAR *agree*
    get high confidence; disagreement (e.g. optical says water but SAR
    backscatter is high -> likely cloud shadow false positive) gets
    flagged explicitly rather than silently resolved.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:
    torch = None
    nn = object


# ---------------------------------------------------------------------------
# Real model (DOFA ViT-Base wavelength-conditioned adapter, reference shape)
# ---------------------------------------------------------------------------

class DOFAAdapter:
    """Thin wrapper matching the GeoChat adapter's load/infer/unload
    lifecycle contract. DOFA's actual architecture (dynamic hypernetwork
    generating per-wavelength patch-embed weights) is intentionally not
    reimplemented here -- pull the official checkpoint/class from the
    DOFA repo and slot it in; this class only owns lifecycle + the
    classification head used for built-up/water/vegetation scoring."""

    def __init__(self, checkpoint_dir, device: str = "cuda"):
        self.checkpoint_dir = checkpoint_dir
        self.device = device
        self.model = None

    def is_available(self) -> bool:
        return torch is not None and torch.cuda.is_available() and self.checkpoint_dir.exists()

    def load(self):
        if torch is None or not torch.cuda.is_available():
            raise RuntimeError("CUDA not available -- DOFA requires a GPU.")
        if not self.checkpoint_dir.exists():
            raise FileNotFoundError(f"No DOFA checkpoint at {self.checkpoint_dir}")
        # Placeholder for the real DOFA class load (see project README for
        # the upstream repo/class to import once weights are downloaded).
        raise NotImplementedError(
            "Wire in the official DOFA model class here once "
            "checkpoints/dofa-vitb is populated; classical_fusion_fallback "
            "below is fully functional in the meantime."
        )

    def unload(self):
        self.model = None


# ---------------------------------------------------------------------------
# Classical fallback: spectral indices + SAR thresholding + agreement map
# ---------------------------------------------------------------------------

@dataclass
class BandMap:
    """Index of which array channel holds which physical band. Adjust to
    match your actual GeoTIFF band order (Sentinel-2 style default)."""
    blue: int = 0
    green: int = 1
    red: int = 2
    nir: int = 3
    swir: int = 4  # optional


def ndwi(optical: np.ndarray, bands: BandMap) -> np.ndarray:
    """Normalized Difference Water Index: (Green - NIR) / (Green + NIR).
    > ~0.2 typically indicates open water."""
    g = optical[bands.green].astype(np.float32)
    nir = optical[bands.nir].astype(np.float32)
    denom = g + nir
    denom[denom == 0] = 1e-6
    return (g - nir) / denom


def ndbi(optical: np.ndarray, bands: BandMap) -> np.ndarray:
    """Normalized Difference Built-up Index using SWIR/NIR when a SWIR
    band is present, else a NIR/Red proxy. > ~0.1 suggests built-up."""
    nir = optical[bands.nir].astype(np.float32)
    if optical.shape[0] > bands.swir:
        swir = optical[bands.swir].astype(np.float32)
        denom = swir + nir
        denom[denom == 0] = 1e-6
        return (swir - nir) / denom
    red = optical[bands.red].astype(np.float32)
    denom = nir + red
    denom[denom == 0] = 1e-6
    return (nir - red) / denom * -1.0  # crude proxy, lower reliability


def sar_water_mask(sar_db: np.ndarray, threshold_db: float = -20.0) -> np.ndarray:
    """Sentinel-1 style sigma-nought (dB). Specular surfaces (calm water)
    scatter radar away from the sensor -> very low backscatter."""
    return (sar_db < threshold_db).astype(np.float32)


def sar_builtup_mask(sar_db: np.ndarray, threshold_db: float = -5.0) -> np.ndarray:
    """Corner-reflector effect from buildings/urban structures ->
    consistently high backscatter."""
    return (sar_db > threshold_db).astype(np.float32)


@dataclass
class FusionResult:
    water_optical: np.ndarray
    water_sar: np.ndarray
    water_agreement: np.ndarray       # both agree: high confidence
    water_disagreement: np.ndarray    # optical says water, SAR disagrees (cloud-shadow flag)
    builtup_optical: np.ndarray
    builtup_sar: np.ndarray
    builtup_agreement: np.ndarray
    cross_modal_consistency_index: float  # 0-1, overall agreement fraction


def classical_fusion_fallback(optical: np.ndarray, sar_db: np.ndarray,
                               bands: BandMap = BandMap(),
                               ndwi_threshold: float = 0.2,
                               ndbi_threshold: float = 0.1) -> FusionResult:
    """Runs full optical+SAR cross-examination with no learned weights.
    sar_db must already be resampled/co-registered to the optical grid
    (shape (H, W) matching optical.shape[1:])."""
    water_opt = (ndwi(optical, bands) > ndwi_threshold).astype(np.float32)
    built_opt = (ndbi(optical, bands) > ndbi_threshold).astype(np.float32)
    water_sar = sar_water_mask(sar_db)
    built_sar = sar_builtup_mask(sar_db)

    water_agree = water_opt * water_sar
    water_disagree = water_opt * (1 - water_sar)  # optical-only water = possible cloud shadow
    built_agree = built_opt * built_sar

    total_px = water_opt.size
    agree_px = np.sum(water_agree > 0) + np.sum(built_agree > 0)
    disagree_px = np.sum(water_disagree > 0)
    consistency = float(agree_px / max(1, agree_px + disagree_px))

    return FusionResult(
        water_optical=water_opt,
        water_sar=water_sar,
        water_agreement=water_agree,
        water_disagreement=water_disagree,
        builtup_optical=built_opt,
        builtup_sar=built_sar,
        builtup_agreement=built_agree,
        cross_modal_consistency_index=round(consistency, 4),
    )
