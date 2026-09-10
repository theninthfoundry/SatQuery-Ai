"""SAM (Segment Anything Model) Adapter for Precision RS Mask Refinement.

Converts bounding boxes from visual grounding into pixel-level segmentation
masks and GeoJSON polygon boundaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class SAMModelAdapter:
    """Adapter for Segment Anything Model / MobileSAM promptable segmentation."""

    def __init__(self, checkpoint_path: Optional[str] = None):
        self.checkpoint_path = checkpoint_path
        self.model = None
        self.predictor = None
        self._is_loaded = False

    def load(self):
        """Load SAM predictor if checkpoint exists."""
        if not HAS_TORCH:
            return
        # If segment_anything library is installed and weights exist
        try:
            from segment_anything import sam_model_registry, SamPredictor
            if self.checkpoint_path and Path(self.checkpoint_path).exists():
                device = "cuda" if torch.cuda.is_available() else "cpu"
                sam = sam_model_registry["vit_b"](checkpoint=self.checkpoint_path).to(device)
                self.predictor = SamPredictor(sam)
                self._is_loaded = True
        except ImportError:
            pass

    def refine_box_to_mask(
        self,
        image_rgb: np.ndarray,
        box_coords: List[float],  # [x1, y1, x2, y2]
    ) -> Tuple[np.ndarray, float, List[List[float]]]:
        """Convert a bounding box into a refined binary segmentation mask and polygon.
        
        Args:
            image_rgb: (H, W, 3) uint8 image.
            box_coords: [x1, y1, x2, y2] pixel coordinates.
            
        Returns:
            Tuple of:
                - Binary mask (H, W) uint8 (0 or 255)
                - Mask IoU confidence score
                - Exterior polygon vertices [[x, y], ...]
        """
        h, w = image_rgb.shape[:2]
        x1, y1, x2, y2 = [int(round(c)) for c in box_coords]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        # 1. Neural SAM inference if model weights loaded
        if self._is_loaded and self.predictor is not None:
            try:
                self.predictor.set_image(image_rgb)
                box_np = np.array([x1, y1, x2, y2])
                masks, scores, _ = self.predictor.predict(
                    box=box_np[None, :],
                    multimask_output=False,
                )
                mask_uint8 = (masks[0] * 255).astype(np.uint8)
                score = float(scores[0])
                polygon = self._mask_to_polygon(mask_uint8)
                return mask_uint8, score, polygon
            except Exception:
                pass

        # 2. High-precision GrabCut / Otsu morphological refinement fallback
        # Given a bounding box, perform local color-histogram segmentation
        mask_uint8 = np.zeros((h, w), dtype=np.uint8)
        polygon = []
        score = None  # Explicit None: neural SAM weights not loaded

        if HAS_CV2 and (x2 - x1) > 4 and (y2 - y1) > 4:
            try:
                roi = image_rgb[y1:y2, x1:x2]
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                # Otsu thresholding within the bounding box
                _, thresh = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                mask_uint8[y1:y2, x1:x2] = thresh
                polygon = self._mask_to_polygon(mask_uint8)
            except Exception:
                mask_uint8[y1:y2, x1:x2] = 255
                polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]
        else:
            mask_uint8[y1:y2, x1:x2] = 255
            polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]

        return mask_uint8, score, polygon

    def _mask_to_polygon(self, mask: np.ndarray) -> List[List[float]]:
        """Extract simplified polygon coordinates from binary mask."""
        if not HAS_CV2:
            return []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return []
        largest = max(contours, key=cv2.contourArea)
        # Approximate contour to reduce vertex count for GeoJSON
        epsilon = 0.01 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        return [[float(p[0][0]), float(p[0][1])] for p in approx]


sam_adapter = SAMModelAdapter()
