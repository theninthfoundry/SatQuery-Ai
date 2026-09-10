"""CDVQA (Change Detection Visual Question Answering) Dataset Adapter.

Evaluates multi-temporal visual question answering over before-and-after image pairs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .adapter import DatasetAdapter, DatasetSample, EvaluationMetricResult


class CDVQAAdapter(DatasetAdapter):
    """Adapter for Change Detection VQA benchmark datasets."""

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> None:
        self.samples = []
        ann_file = self.dataset_dir / f"cdvqa_{split}.json"
        images_dir = self.dataset_dir / "pairs"

        if not ann_file.exists():
            return

        try:
            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                sid = str(item.get("id", len(self.samples)))
                t1_path = images_dir / item.get("image_t1", f"{sid}_t1.tif")
                t2_path = images_dir / item.get("image_t2", f"{sid}_t2.tif")

                self.samples.append(DatasetSample(
                    sample_id=sid,
                    image_paths=[t1_path, t2_path],
                    question=item.get("question", ""),
                    ground_truth_answer=str(item.get("answer", "")),
                    metadata={
                        "change_type": item.get("change_type", "general"),
                        "has_change": item.get("has_change", True),
                    },
                ))
                if max_samples and len(self.samples) >= max_samples:
                    break
        except Exception:
            pass

        self._is_loaded = True

    def evaluate(self, predictions: List[Dict[str, Any]]) -> EvaluationMetricResult:
        pred_map = {str(p["sample_id"]): str(p.get("prediction", "")).strip().lower() for p in predictions}

        correct = 0
        total = 0

        for sample in self.samples:
            sid = sample.sample_id
            if sid not in pred_map:
                continue

            pred = re.sub(r"[^\w\s]", "", pred_map[sid])
            gt = re.sub(r"[^\w\s]", "", (sample.ground_truth_answer or "").lower().strip())

            if pred == gt or gt in pred:
                correct += 1
            total += 1

        acc = (correct / max(1, total)) if total > 0 else 0.0

        return EvaluationMetricResult(
            dataset_name="CDVQA",
            sample_count=total,
            primary_metric_name="Top-1 Accuracy",
            primary_metric_value=acc,
            all_metrics={"accuracy": acc},
        )
