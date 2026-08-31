"""
SAR backscatter change proxy.

Deliberately NOT a learned model. This is the honest version of "optical +
SAR analysis" the PRD settled on (Section 7.4): an independent, explainable
statistic to cross-check against the optical change result — a log-ratio
between two SAR intensity images, thresholded — not a black-box fusion
model. No training, no checkpoint, no "untrained" caveat needed, because
there's nothing learned here to be untrained.

Real SAR imagery (Sentinel-1, RISAT) is typically stored as calibrated
backscatter intensity (sigma-nought) in a non-8-bit format; this reads
whatever's on disk as a single-channel intensity image via PIL, which is
correct for an 8-bit preview/demo product but not for calibrated SAR
products — swap _load_intensity for a rasterio-based reader that reads
actual backscatter values once real SAR data is wired in (PRD Section 9).
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np
from PIL import Image


class SARChangeProxy:
    def __init__(self, image_size: int = 128, log_ratio_threshold: float = 0.3) -> None:
        self.image_size = image_size
        self.threshold = log_ratio_threshold

    def _load_intensity(self, path: str) -> np.ndarray:
        img = Image.open(path).convert("L").resize((self.image_size, self.image_size))
        return np.asarray(img, dtype=np.float32) + 1.0  # +1 avoids log(0)

    def compute(self, before_path: str, after_path: str) -> Dict[str, Any]:
        before = self._load_intensity(before_path)
        after = self._load_intensity(after_path)

        log_ratio = np.abs(np.log(after) - np.log(before))
        changed_mask = log_ratio > self.threshold
        sar_change_percent = round(float(changed_mask.mean()) * 100, 2)

        return {
            "sar_change_percent": sar_change_percent,
            "mean_log_ratio": round(float(log_ratio.mean()), 4),
        }
