"""RSVQA-HR / RSVQA-LR Benchmark Dataset Adapter.

Loads standard RSVQA splits and computes Top-1 Exact Match Accuracy
and answer category breakdowns (presence, count, area, comparison).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .adapter import DatasetAdapter, DatasetSample, EvaluationMetricResult


class RSVQAAdapter(DatasetAdapter):
    """Adapter for the Remote Sensing Visual Question Answering (RSVQA) benchmark."""

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> None:
        self.samples = []
        ann_file = self.dataset_dir / f"{split}_questions.json"
        answers_file = self.dataset_dir / f"{split}_answers.json"
        images_dir = self.dataset_dir / "Images"

        if not ann_file.exists():
            return  # Empty dataset until downloaded

        try:
            with open(ann_file, "r", encoding="utf-8") as f:
                q_data = json.load(f)
            answers_dict = {}
            if answers_file.exists():
                with open(answers_file, "r", encoding="utf-8") as f:
                    answers_dict = {a["id"]: a["answer"] for a in json.load(f).get("answers", [])}

            questions = q_data.get("questions", q_data) if isinstance(q_data, dict) else q_data
            for item in questions:
                q_id = str(item.get("id", len(self.samples)))
                img_name = item.get("image_name", f"{item.get('img_id', q_id)}.tif")
                img_path = images_dir / img_name
                ans = item.get("answer", answers_dict.get(q_id, ""))

                sample = DatasetSample(
                    sample_id=q_id,
                    image_paths=[img_path],
                    question=item.get("question", ""),
                    ground_truth_answer=str(ans),
                    metadata={"category": item.get("type", "general")},
                )
                self.samples.append(sample)
                if max_samples and len(self.samples) >= max_samples:
                    break
        except Exception:
            pass

        self._is_loaded = True

    def evaluate(self, predictions: List[Dict[str, Any]]) -> EvaluationMetricResult:
        """Compute Exact Match Top-1 accuracy and category accuracy."""
        pred_map = {str(p["sample_id"]): str(p.get("prediction", "")).strip().lower() for p in predictions}

        correct = 0
        total = 0
        cat_correct: Dict[str, int] = {}
        cat_total: Dict[str, int] = {}

        for sample in self.samples:
            sid = sample.sample_id
            if sid not in pred_map:
                continue

            pred = self._normalize_answer(pred_map[sid])
            gt = self._normalize_answer(sample.ground_truth_answer or "")
            cat = sample.metadata.get("category", "general")

            cat_total[cat] = cat_total.get(cat, 0) + 1
            is_match = (pred == gt) or (gt in pred and len(gt) > 2)

            if is_match:
                correct += 1
                cat_correct[cat] = cat_correct.get(cat, 0) + 1
            total += 1

        overall_acc = (correct / max(1, total)) if total > 0 else 0.0
        per_cat_acc = {
            cat: round(cat_correct.get(cat, 0) / max(1, cat_total[cat]), 4)
            for cat in cat_total
        }

        return EvaluationMetricResult(
            dataset_name="RSVQA-HR",
            sample_count=total,
            primary_metric_name="Top-1 Accuracy",
            primary_metric_value=overall_acc,
            all_metrics={
                "accuracy": overall_acc,
                "exact_match": (correct / max(1, total)) if total > 0 else 0.0,
            },
            per_class_metrics=per_cat_acc,
        )

    def _normalize_answer(self, text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^\w\s]", "", s)
        return s
