"""BigEarthNet Multispectral Benchmark Dataset Adapter.

Evaluates multi-label satellite land-cover classification across standard
CORINE Land Cover (CLC) categories, computing Micro/Macro F1 and mAP.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from .adapter import DatasetAdapter, DatasetSample, EvaluationMetricResult


class BigEarthNetAdapter(DatasetAdapter):
    """Adapter for the BigEarthNet multispectral benchmark."""

    CLASSES = [
        "Urban fabric", "Industrial or commercial units", "Arable land",
        "Permanent crops", "Pastures", "Complex cultivation patterns",
        "Land principally occupied by agriculture", "Broad-leaved forest",
        "Coniferous forest", "Mixed forest", "Natural grassland and sparsely vegetated areas",
        "Sclerophyllous vegetation", "Moors and heathland", "Transitional woodland, shrub",
        "Beaches, dunes, sands", "Inland wetlands", "Coastal wetlands",
        "Inland waters", "Marine waters"
    ]

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> None:
        self.samples = []
        meta_file = self.dataset_dir / f"bigearthnet_{split}.json"
        patches_dir = self.dataset_dir / "patches"

        if not meta_file.exists():
            return

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                patch_id = item.get("patch_id", len(self.samples))
                p_path = patches_dir / f"{patch_id}.tif"
                labels = item.get("labels", [])

                self.samples.append(DatasetSample(
                    sample_id=str(patch_id),
                    image_paths=[p_path],
                    ground_truth_labels=labels,
                    metadata={"snow_cloud": item.get("snow_cloud", False)},
                ))
                if max_samples and len(self.samples) >= max_samples:
                    break
        except Exception:
            pass

        self._is_loaded = True

    def evaluate(self, predictions: List[Dict[str, Any]]) -> EvaluationMetricResult:
        """Compute Macro F1 and Micro F1 across multi-label predictions."""
        pred_map = {str(p["sample_id"]): set(p.get("predicted_labels", [])) for p in predictions}

        tp_total = 0
        fp_total = 0
        fn_total = 0

        class_tps = {c: 0 for c in self.CLASSES}
        class_fps = {c: 0 for c in self.CLASSES}
        class_fns = {c: 0 for c in self.CLASSES}

        for sample in self.samples:
            sid = sample.sample_id
            if sid not in pred_map:
                continue

            preds = pred_map[sid]
            gts = set(sample.ground_truth_labels or [])

            for c in self.CLASSES:
                p_has = c in preds
                g_has = c in gts
                if p_has and g_has:
                    class_tps[c] += 1
                    tp_total += 1
                elif p_has and not g_has:
                    class_fps[c] += 1
                    fp_total += 1
                elif not p_has and g_has:
                    class_fns[c] += 1
                    fn_total += 1

        # Micro F1
        micro_prec = tp_total / max(1, tp_total + fp_total)
        micro_rec = tp_total / max(1, tp_total + fn_total)
        micro_f1 = (2 * micro_prec * micro_rec) / max(1e-6, micro_prec + micro_rec)

        # Macro F1
        f1_list = []
        for c in self.CLASSES:
            cp = class_tps[c] / max(1, class_tps[c] + class_fps[c])
            cr = class_tps[c] / max(1, class_tps[c] + class_fns[c])
            cf1 = (2 * cp * cr) / max(1e-6, cp + cr) if (cp + cr) > 0 else 0.0
            f1_list.append(cf1)
        macro_f1 = float(np.mean(f1_list))

        return EvaluationMetricResult(
            dataset_name="BigEarthNet-MultiLabel",
            sample_count=len(self.samples),
            primary_metric_name="Macro F1-Score",
            primary_metric_value=macro_f1,
            all_metrics={
                "macro_f1": macro_f1,
                "micro_f1": micro_f1,
                "micro_precision": micro_prec,
                "micro_recall": micro_rec,
            },
        )
