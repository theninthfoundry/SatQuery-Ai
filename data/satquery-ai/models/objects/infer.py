"""
Inference wrapper for object-count density regression.

Count = sum of the predicted density map (standard for this approach).
Box locations = connected components on a thresholded density map, each
given a small fixed-radius box — these are approximate positions from a
counting model, not learned box sizes from a real detector. Honest about
that in the returned schema (each box has no meaningful width/height
signal beyond the fixed radius).
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
from PIL import Image

from .model import ObjectCountNet

_DEFAULT_CHECKPOINT = Path(__file__).parent / "checkpoints" / "best.pt"


class ObjectCounter:
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        image_size: int = 64,
        peak_threshold_ratio: float = 0.15,
        box_radius: int = 3,
    ) -> None:
        self.image_size = image_size
        self.peak_threshold_ratio = peak_threshold_ratio
        self.box_radius = box_radius
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ObjectCountNet().to(self.device)

        path = Path(checkpoint_path) if checkpoint_path else _DEFAULT_CHECKPOINT
        self.is_trained = path.exists()
        if self.is_trained:
            self.model.load_state_dict(torch.load(path, map_location=self.device))
        else:
            warnings.warn(
                f"No checkpoint found at {path} — running an UNTRAINED model. "
                "Output is structurally valid but not meaningful until you train "
                "on real data (see models/objects/train.py).",
                stacklevel=2,
            )
        self.model.eval()

    def count(self, image_path: str) -> Dict[str, Any]:
        img = Image.open(image_path).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(self.device)

        with torch.no_grad():
            density = self.model(tensor)[0, 0].cpu().numpy()

        count = round(float(density.sum()))
        boxes = self._density_to_boxes(density)

        return {
            "count": max(count, 0),
            "boxes": boxes,
            "confidence": round(float(min(1.0, density.max())), 2) if density.max() > 0 else 0.0,
            "is_trained": self.is_trained,
        }

    def _density_to_boxes(self, density: np.ndarray) -> List[Dict[str, Any]]:
        peak_value = density.max()
        if peak_value <= 0:
            return []

        threshold = peak_value * self.peak_threshold_ratio
        binary = (density > threshold).astype(np.uint8)
        num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        boxes = []
        r = self.box_radius
        for label in range(1, num_labels):  # label 0 is background
            if stats[label, cv2.CC_STAT_AREA] < 1:
                continue
            cx, cy = centroids[label]
            boxes.append(
                {
                    "type": "Feature",
                    "properties": {"source": "density-peak", "box_radius_px": r},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [cx - r, cy - r],
                                [cx + r, cy - r],
                                [cx + r, cy + r],
                                [cx - r, cy + r],
                                [cx - r, cy - r],
                            ]
                        ],
                    },
                }
            )
        return boxes
