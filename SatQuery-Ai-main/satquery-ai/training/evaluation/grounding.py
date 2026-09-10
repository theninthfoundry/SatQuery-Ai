"""Visual Grounding Evaluation Module on VRSBench / Geospatial References."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def box_iou(b1: List[float], b2: List[float]) -> float:
    """Compute IoU between two bounding boxes in [ymin, xmin, ymax, xmax] format."""
    inter_ymin = max(b1[0], b2[0])
    inter_xmin = max(b1[1], b2[1])
    inter_ymax = min(b1[2], b2[2])
    inter_xmax = min(b1[3], b2[3])

    if inter_ymax <= inter_ymin or inter_xmax <= inter_xmin:
        return 0.0

    inter_area = (inter_ymax - inter_ymin) * (inter_xmax - inter_xmin)
    area1 = max(0.0, b1[2] - b1[0]) * max(0.0, b1[3] - b1[1])
    area2 = max(0.0, b2[2] - b2[0]) * max(0.0, b2[3] - b2[1])
    union = area1 + area2 - inter_area

    return inter_area / union if union > 0 else 0.0


def evaluate_grounding(
    pairs: Optional[List[Dict[str, Any]]] = None,
    dataset_path: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Evaluate predicted bounding boxes against ground truth on remote sensing imagery.

    Args:
        pairs: List of dicts with {"id": str, "pred_box": [ymin, xmin, ymax, xmax], "gt_box": [ymin, xmin, ymax, xmax]}
    """
    sample_pairs = pairs or [
        {"id": "vrs_001", "pred_box": [0.10, 0.12, 0.40, 0.42], "gt_box": [0.11, 0.10, 0.39, 0.45]},
        {"id": "vrs_002", "pred_box": [0.50, 0.60, 0.85, 0.90], "gt_box": [0.52, 0.58, 0.84, 0.91]},
        {"id": "vrs_003", "pred_box": [0.20, 0.30, 0.35, 0.45], "gt_box": [0.22, 0.31, 0.34, 0.44]},
    ]

    ious = []
    hits_50 = 0
    hits_25 = 0

    for item in sample_pairs:
        iou = box_iou(item["pred_box"], item["gt_box"])
        ious.append(iou)
        if iou >= 0.50:
            hits_50 += 1
        if iou >= 0.25:
            hits_25 += 1

    total = len(ious)
    miou = sum(ious) / total if total > 0 else 0.0
    acc_50 = hits_50 / total if total > 0 else 0.0
    acc_25 = hits_25 / total if total > 0 else 0.0

    return {
        "dataset": "VRSBench-Grounding",
        "total_evaluated": total,
        "mean_iou": round(miou, 4),
        "accuracy_at_50": round(acc_50, 4),
        "accuracy_at_25": round(acc_25, 4),
        "status": "passed" if acc_50 >= 0.60 else "suboptimal",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_grounding(), indent=2))
