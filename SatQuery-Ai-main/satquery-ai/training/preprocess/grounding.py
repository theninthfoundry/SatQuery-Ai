"""Visual grounding bounding box coordinates and mask utilities."""

import numpy as np
from typing import Dict, Tuple, List


def normalize_bbox(
    ymin: float,
    xmin: float,
    ymax: float,
    xmax: float,
    height: int,
    width: int,
) -> Dict[str, float]:
    """Convert absolute pixel coordinates to normalized [0.0, 1.0]."""
    return {
        "ymin": round(max(0.0, min(1.0, ymin / height)), 4),
        "xmin": round(max(0.0, min(1.0, xmin / width)), 4),
        "ymax": round(max(0.0, min(1.0, ymax / height)), 4),
        "xmax": round(max(0.0, min(1.0, xmax / width)), 4),
    }


def denormalize_bbox(
    box: Dict[str, float],
    height: int,
    width: int,
) -> Tuple[int, int, int, int]:
    """Convert normalized box to absolute pixel coordinates (ymin, xmin, ymax, xmax)."""
    return (
        int(box["ymin"] * height),
        int(box["xmin"] * width),
        int(box["ymax"] * height),
        int(box["xmax"] * width),
    )


def rasterize_bbox_to_mask(
    boxes: List[Dict[str, float]],
    height: int,
    width: int,
) -> np.ndarray:
    """Rasterize a list of normalized bounding boxes into a binary 2D mask."""
    mask = np.zeros((height, width), dtype=np.uint8)
    for b in boxes:
        ymin, xmin, ymax, xmax = denormalize_bbox(b, height, width)
        mask[ymin:ymax, xmin:xmax] = 1
    return mask
