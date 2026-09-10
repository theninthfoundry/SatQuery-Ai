"""VRSBench Dataset Adapter for Visual Remote Sensing Grounding.

Evaluates bounding box localization predictions using spatial Intersection over
Union (IoU) and computes mAP@0.50 and mAP@0.75.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from .adapter import DatasetAdapter, DatasetSample, EvaluationMetricResult


class VRSBenchAdapter(DatasetAdapter):
    """Adapter for the VRSBench visual grounding benchmark."""

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> None:
        self.samples = []
        ann_file = self.dataset_dir / f"vrsbench_grounding_{split}.json"
        images_dir = self.dataset_dir / "images"

        if not ann_file.exists():
            return

        try:
            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                s_id = str(item.get("id", len(self.samples)))
                img_path = images_dir / item.get("image_name", f"{s_id}.png")
                gt_boxes = item.get("bboxes", [])

                self.samples.append(DatasetSample(
                    sample_id=s_id,
                    image_paths=[img_path],
                    referring_expression=item.get("expression", item.get("prompt", "")),
                    ground_truth_boxes=gt_boxes,
                    metadata={"category": item.get("category", "object")},
                ))
                if max_samples and len(self.samples) >= max_samples:
                    break
        except Exception:
            pass

        self._is_loaded = True

    def evaluate(self, predictions: List[Dict[str, Any]]) -> EvaluationMetricResult:
        """Compute mAP@0.50 and mAP@0.75 across bounding box predictions."""
        pred_map = {str(p["sample_id"]): p.get("boxes", []) for p in predictions}

        ious_at_50 = []
        ious_at_75 = []
        all_max_ious = []

        for sample in self.samples:
            sid = sample.sample_id
            if sid not in pred_map:
                continue

            pred_boxes = pred_map[sid]
            gt_boxes = sample.ground_truth_boxes or []

            if not gt_boxes:
                continue

            max_iou = 0.0
            for pb in pred_boxes:
                for gb in gt_boxes:
                    iou = self._box_iou(pb, gb)
                    if iou > max_iou:
                        max_iou = iou

            all_max_ious.append(max_iou)
            ious_at_50.append(1.0 if max_iou >= 0.50 else 0.0)
            ious_at_75.append(1.0 if max_iou >= 0.75 else 0.0)

        total = len(all_max_ious)
        map_50 = float(np.mean(ious_at_50)) if total > 0 else 0.0
        map_75 = float(np.mean(ious_at_75)) if total > 0 else 0.0
        mean_iou = float(np.mean(all_max_ious)) if total > 0 else 0.0

        return EvaluationMetricResult(
            dataset_name="VRSBench-Grounding",
            sample_count=total,
            primary_metric_name="mAP@0.50",
            primary_metric_value=map_50,
            all_metrics={
                "map_50": map_50,
                "map_75": map_75,
                "mean_iou": mean_iou,
            },
        )

    def _box_iou(self, boxA: List[float], boxB: List[float]) -> float:
        """Compute IoU between two [x1, y1, x2, y2] boxes."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = max(0.0, (boxA[2] - boxA[0])) * max(0.0, (boxA[3] - boxA[1]))
        boxBArea = max(0.0, (boxB[2] - boxB[0])) * max(0.0, (boxB[3] - boxB[1]))

        denom = float(boxAArea + boxBArea - interArea)
        return float(interArea / denom) if denom > 0 else 0.0
