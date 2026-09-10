"""Benchmark Dataset Adapters for Remote Sensing Evaluation."""

from .adapter import DatasetAdapter, DatasetSample, EvaluationMetricResult
from .rsvqa import RSVQAAdapter
from .vrsbench import VRSBenchAdapter
from .cdvqa import CDVQAAdapter
from .bigearthnet import BigEarthNetAdapter

__all__ = [
    "DatasetAdapter",
    "DatasetSample",
    "EvaluationMetricResult",
    "RSVQAAdapter",
    "VRSBenchAdapter",
    "CDVQAAdapter",
    "BigEarthNetAdapter",
]
