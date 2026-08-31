"""
Inference wrapper for the change-detection model.

Loads a trained checkpoint if one exists at the given path; otherwise runs
the untrained architecture and warns loudly rather than pretending the
output means anything. Converts the predicted mask to pixel-space polygon
contours (OpenCV) rather than true geo-referenced GeoJSON — real
georeferencing needs the source raster's affine transform, which isn't
wired up until Phase 1's geospatial pipeline (PRD Section 9) lands. Swap
`_mask_to_pixel_polygons` for a rasterio-based version once that exists;
nothing else in this file should need to change.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
from PIL import Image

from .model import ChangeDetectionNet

_DEFAULT_CHECKPOINT = Path(__file__).parent / "checkpoints" / "best.pt"


class ChangeDetector:
    def __init__(self, checkpoint_path: Optional[str] = None, image_size: int = 256) -> None:
        self.image_size = image_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ChangeDetectionNet().to(self.device)

        path = Path(checkpoint_path) if checkpoint_path else _DEFAULT_CHECKPOINT
        self.is_trained = path.exists()
        if self.is_trained:
            self.model.load_state_dict(torch.load(path, map_location=self.device))
        else:
            warnings.warn(
                f"No checkpoint found at {path} — running an UNTRAINED model. "
                "Output is structurally valid but not meaningful until you train "
                "on real data (see models/change/train.py).",
                stacklevel=2,
            )
        self.model.eval()

    def _load(self, path: str) -> torch.Tensor:
        img = Image.open(path).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

    def detect(self, image_before_path: str, image_after_path: str, threshold: float = 0.5) -> Dict[str, Any]:
        img_a = self._load(image_before_path).to(self.device)
        img_b = self._load(image_after_path).to(self.device)

        with torch.no_grad():
            logits = self.model(img_a, img_b)
            probs = torch.sigmoid(logits)[0, 0].cpu().numpy()

        mask = (probs > threshold).astype(np.uint8)
        change_percent = round(float(mask.mean()) * 100, 2)
        model_confidence = round(float(probs[mask.astype(bool)].mean()), 2) if mask.any() else 0.0

        return {
            "change_percent": change_percent,
            "changed_regions": {"type": "FeatureCollection", "features": self._mask_to_pixel_polygons(mask)},
            "model_confidence": model_confidence,
            "is_trained": self.is_trained,
        }

    @staticmethod
    def _mask_to_pixel_polygons(mask: np.ndarray) -> List[Dict[str, Any]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        features = []
        for contour in contours:
            if cv2.contourArea(contour) < 4:
                continue
            coords = contour.squeeze(1).tolist()
            if len(coords) < 3:
                continue
            coords.append(coords[0])  # close the ring
            features.append(
                {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [coords]}}
            )
        return features
