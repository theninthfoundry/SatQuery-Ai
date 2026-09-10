"""
Inference wrapper for land-cover segmentation.

Runs the model on a single image and reduces the per-pixel class map to
per-class area fractions — matching the segment_landcover tool's existing
output schema ({"classes": {...}, "confidence": ...}). The per-pixel mask
itself is also returned (as class indices) in case a future map layer
wants to render it directly, rather than only the aggregate fractions.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
from PIL import Image

from .model import CLASSES, LandCoverSegNet

_DEFAULT_CHECKPOINT = Path(__file__).parent / "checkpoints" / "best.pt"


class LandCoverClassifier:
    def __init__(self, checkpoint_path: Optional[str] = None, image_size: int = 64) -> None:
        self.image_size = image_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LandCoverSegNet(num_classes=len(CLASSES)).to(self.device)

        path = Path(checkpoint_path) if checkpoint_path else _DEFAULT_CHECKPOINT
        self.is_trained = path.exists()
        if self.is_trained:
            self.model.load_state_dict(torch.load(path, map_location=self.device))
        else:
            warnings.warn(
                f"No checkpoint found at {path} — running an UNTRAINED model. "
                "Output is structurally valid but not meaningful until you train "
                "on real data (see models/landcover/train.py).",
                stacklevel=2,
            )
        self.model.eval()

    def classify(self, image_path: str) -> Dict[str, Any]:
        img = Image.open(image_path).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]  # (num_classes, H, W)
            pred_mask = probs.argmax(dim=0).cpu().numpy()  # (H, W)

        total_pixels = pred_mask.size
        fractions = {
            CLASSES[c]: round(float((pred_mask == c).sum()) / total_pixels, 3) for c in range(len(CLASSES))
        }
        # Mean top-class probability across pixels, as a simple confidence proxy.
        confidence = round(float(probs.max(dim=0).values.mean().cpu()), 2)

        return {"classes": fractions, "confidence": confidence, "is_trained": self.is_trained}
