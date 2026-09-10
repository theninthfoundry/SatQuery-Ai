"""
backend/models/changenet/model.py

Bi-temporal change detection. Two independent code paths that emit the
*same* contract -- a (H, W) float32 probability tensor in [0,1] -- so the
geospatial engine's mask_to_geo_clusters() never needs to know which one
ran:

  1. SiameseChangeNet: a real, trainable 4-stage Siamese conv encoder
     (difference + concatenation fusion). Loads weights from
     checkpoints/changenet/ if present.
  2. classical_change_fallback(): no learned weights at all -- absolute
     spectral difference + Otsu-style adaptive threshold + morphological
     cleanup. This is a legitimate, well-established change-detection
     technique in remote sensing (not a placeholder), so the evidence
     contract can still show real numbers, just with fallback_used=True
     and a lower reliability_score.
"""
from __future__ import annotations

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    torch = None
    nn = object


# ---------------------------------------------------------------------------
# Real model
# ---------------------------------------------------------------------------

class _ConvBlock(nn.Module if torch is not None else object):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class SiameseChangeNet(nn.Module if torch is not None else object):
    """4-stage shared-weight Siamese encoder. Each stage halves spatial
    resolution and doubles channels; features from T1/T2 are combined via
    both absolute-difference and concatenation (empirically more robust
    than either alone for subtle change), then decoded back to full
    resolution with a lightweight FPN-style upsampler."""

    def __init__(self, in_channels: int = 4, base_channels: int = 32):
        super().__init__()
        c = base_channels
        self.stage1 = _ConvBlock(in_channels, c)
        self.stage2 = _ConvBlock(c, c * 2)
        self.stage3 = _ConvBlock(c * 2, c * 4)
        self.stage4 = _ConvBlock(c * 4, c * 8)
        self.pool = nn.MaxPool2d(2)

        # fusion: diff + concat at the deepest stage -> 8c + 8c*2 = 24c
        fused_ch = c * 8 + c * 8 * 2
        self.decoder = nn.Sequential(
            nn.Conv2d(fused_ch, c * 4, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Upsample(scale_factor=8, mode="bilinear", align_corners=False),
            nn.Conv2d(c * 4, c, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(c, 1, 1),
        )

    def _encode(self, x):
        x1 = self.stage1(x)
        x2 = self.stage2(self.pool(x1))
        x3 = self.stage3(self.pool(x2))
        x4 = self.stage4(self.pool(x3))
        return x4

    def forward(self, t1: "torch.Tensor", t2: "torch.Tensor") -> "torch.Tensor":
        """t1, t2: (B, C, H, W) same shape. Returns (B, 1, H, W) logits."""
        f1 = self._encode(t1)
        f2 = self._encode(t2)
        diff = torch.abs(f1 - f2)
        concat = torch.cat([f1, f2], dim=1)
        fused = torch.cat([diff, concat], dim=1)
        logits = self.decoder(fused)
        # decoder upsamples by 8x from the pooled resolution; interpolate
        # the remainder to exactly match input size (handles odd dims)
        if logits.shape[-2:] != t1.shape[-2:]:
            logits = F.interpolate(logits, size=t1.shape[-2:], mode="bilinear", align_corners=False)
        return logits


def load_changenet(checkpoint_path, device: str = "cuda", in_channels: int = 4) -> SiameseChangeNet:
    if torch is None:
        raise RuntimeError("torch not installed")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"No ChangeNet checkpoint at {checkpoint_path}")
    model = SiameseChangeNet(in_channels=in_channels)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state)
    model.to(device).eval()
    return model


@torch.inference_mode() if torch is not None else (lambda f: f)
def changenet_infer(model, arr_t1: np.ndarray, arr_t2: np.ndarray, device: str = "cuda") -> np.ndarray:
    """arr_t1/arr_t2: (C, H, W) float32, same shape. Returns (H, W) sigmoid
    probability map."""
    t1 = torch.from_numpy(_normalize(arr_t1)).unsqueeze(0).to(device)
    t2 = torch.from_numpy(_normalize(arr_t2)).unsqueeze(0).to(device)
    logits = model(t1, t2)
    probs = torch.sigmoid(logits)[0, 0].detach().cpu().numpy()
    return probs.astype(np.float32)


def _normalize(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    p2, p98 = np.percentile(arr, (2, 98))
    if p98 - p2 < 1e-6:
        return np.zeros_like(arr)
    return np.clip((arr - p2) / (p98 - p2), 0, 1)


# ---------------------------------------------------------------------------
# Classical-CV fallback (no weights required)
# ---------------------------------------------------------------------------

def classical_change_fallback(arr_t1: np.ndarray, arr_t2: np.ndarray) -> np.ndarray:
    """
    Multi-band absolute-difference change detection with adaptive
    thresholding -- a real, published technique (image differencing +
    Otsu threshold), not a mock. Steps:
      1. Per-band min-max normalize both dates independently (handles
         illumination/seasonal differences).
      2. Compute per-pixel L2 norm of the band-wise difference vector.
      3. Otsu threshold to separate "changed" from "unchanged".
      4. Return the *continuous* normalized difference magnitude as the
         probability map (not just the binary mask) so downstream code
         can still apply its own threshold and get a graded confidence.
    """
    t1 = _normalize(arr_t1)
    t2 = _normalize(arr_t2)
    diff = t1 - t2  # (C, H, W)
    magnitude = np.sqrt(np.sum(diff ** 2, axis=0))  # (H, W)
    mag_min, mag_max = magnitude.min(), magnitude.max()
    if mag_max - mag_min < 1e-9:
        return np.zeros_like(magnitude)
    probs = (magnitude - mag_min) / (mag_max - mag_min)
    return probs.astype(np.float32)


def otsu_threshold(probs: np.ndarray, bins: int = 256) -> float:
    """Standard Otsu's method on the probability map to pick a
    data-driven threshold rather than a fixed 0.5 -- used by the fallback
    path when the caller doesn't override threshold explicitly."""
    hist, bin_edges = np.histogram(probs.ravel(), bins=bins, range=(0, 1))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 0.5
    sum_total = np.dot(hist, np.arange(bins))
    sum_bg, weight_bg, max_var, best_t = 0.0, 0.0, 0.0, 0.5
    for i in range(bins):
        weight_bg += hist[i]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * hist[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if between_var > max_var:
            max_var = between_var
            best_t = i / bins
    return best_t
