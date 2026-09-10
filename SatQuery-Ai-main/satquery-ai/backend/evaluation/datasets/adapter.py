"""Abstract Base Class for Remote Sensing Benchmark Dataset Adapters.

Standardizes loading, splitting, iteration, and evaluation metrics computation
across RSVQA-HR, VRSBench, CDVQA, and BigEarthNet.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator


@dataclass
class DatasetSample:
    """A standardized sample from an Earth observation benchmark dataset."""
    sample_id: str
    image_paths: List[Path]
    question: Optional[str] = None
    referring_expression: Optional[str] = None
    ground_truth_answer: Optional[str] = None
    ground_truth_boxes: Optional[List[List[float]]] = None  # [[x1, y1, x2, y2], ...]
    ground_truth_mask_path: Optional[Path] = None
    ground_truth_labels: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationMetricResult:
    """Aggregated evaluation metrics for an evaluation run."""
    dataset_name: str
    sample_count: int
    primary_metric_name: str
    primary_metric_value: float
    all_metrics: Dict[str, float]
    per_class_metrics: Optional[Dict[str, float]] = None
    evaluation_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "sample_count": self.sample_count,
            "primary_metric": {
                "name": self.primary_metric_name,
                "value": round(self.primary_metric_value, 4),
            },
            "all_metrics": {k: round(v, 4) for k, v in self.all_metrics.items()},
            "per_class_metrics": self.per_class_metrics,
            "metadata": self.evaluation_metadata,
        }


class DatasetAdapter(ABC):
    """Abstract interface for all remote sensing benchmark dataset loaders."""

    def __init__(self, dataset_dir: Path | str):
        self.dataset_dir = Path(dataset_dir)
        self.samples: List[DatasetSample] = []
        self._is_loaded = False

    @abstractmethod
    def load(self, split: str = "test", max_samples: Optional[int] = None) -> None:
        """Load dataset annotations and index file paths into memory."""
        pass

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> DatasetSample:
        return self.samples[idx]

    def __iter__(self) -> Iterator[DatasetSample]:
        return iter(self.samples)

    @abstractmethod
    def evaluate(self, predictions: List[Dict[str, Any]]) -> EvaluationMetricResult:
        """Compute task-specific ground-truth evaluation metrics against predictions."""
        pass
