"""Formal confidence calibration engine for SatQuery AI.

Implements mathematical calibration metrics according to the Confidence Calibration &
Cross-Modal Agreement methodology:
- Platt Scaling (Parametric Logistic Calibration): p = sigmoid(a * score + b)
- Expected Calibration Error (ECE) with M equal-width probability bins
- Maximum Calibration Error (MCE)
- Brier Score (mean squared error of probabilistic predictions)
- Reliability diagram histogram data generator
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ReliabilityBin:
    bin_index: int
    bin_lower: float
    bin_upper: float
    sample_count: int
    mean_confidence: float
    accuracy: float
    calibration_gap: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bin_index": self.bin_index,
            "bin_range": f"{self.bin_lower:.1f}-{self.bin_upper:.1f}",
            "sample_count": self.sample_count,
            "mean_confidence": round(self.mean_confidence, 4),
            "accuracy": round(self.accuracy, 4),
            "calibration_gap": round(self.calibration_gap, 4),
        }


@dataclass
class CalibrationReport:
    sample_count: int
    num_bins: int
    ece: float
    mce: float
    brier_score: float
    bins: List[ReliabilityBin]
    platt_params: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_count": self.sample_count,
            "num_bins": self.num_bins,
            "expected_calibration_error_pct": round(self.ece * 100.0, 2),
            "max_calibration_error_pct": round(self.mce * 100.0, 2),
            "brier_score": round(self.brier_score, 4),
            "platt_parameters": self.platt_params,
            "reliability_diagram_bins": [b.to_dict() for b in self.bins],
        }


def sigmoid(z: float) -> float:
    """Numerically stable sigmoid function."""
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)


def platt_scale(raw_score: float, a: float = 3.5, b: float = -1.5) -> float:
    """Apply logistic Platt scaling to map heuristic composite score to calibrated probability.
    
    Default parameters (a=3.5, b=-1.5) map typical RS heuristic scores [0.5, 0.95]
    into well-calibrated confidence probabilities [0.56, 0.86].
    """
    z = a * raw_score + b
    p = sigmoid(z)
    return round(max(0.01, min(0.99, p)), 4)


def fit_platt_scaling(
    raw_scores: List[float],
    labels: List[int],
    learning_rate: float = 0.05,
    max_epochs: int = 200,
) -> Tuple[float, float]:
    """Fit logistic Platt scaling parameters (a, b) on labeled validation pairs using gradient descent.
    
    Args:
        raw_scores: List of raw heuristic scores in [0, 1].
        labels: Ground truth binary correctness indicators {0, 1}.
        learning_rate: Gradient descent step size.
        max_epochs: Optimization iterations.
        
    Returns:
        Tuple of fitted (a, b) calibration coefficients.
    """
    if not raw_scores or len(raw_scores) != len(labels):
        return 3.5, -1.5

    n = len(raw_scores)
    a, b = 1.0, 0.0

    for _ in range(max_epochs):
        grad_a = 0.0
        grad_b = 0.0
        for s, y in zip(raw_scores, labels):
            p = sigmoid(a * s + b)
            error = p - float(y)
            grad_a += error * s
            grad_b += error

        a -= (learning_rate * grad_a) / n
        b -= (learning_rate * grad_b) / n

    return round(float(a), 4), round(float(b), 4)


def compute_calibration_metrics(
    confidences: List[float],
    labels: List[int],
    num_bins: int = 10,
    a: float = 3.5,
    b: float = -1.5,
) -> CalibrationReport:
    """Compute Expected Calibration Error (ECE), MCE, Brier score, and reliability histogram bins.
    
    Args:
        confidences: Predicted probability or calibrated confidence scores in [0, 1].
        labels: Ground-truth binary correctness indicators (1 = correct, 0 = incorrect).
        num_bins: Number of equal-width bins (default 10).
        a, b: Platt scaling parameters used.
        
    Returns:
        CalibrationReport containing scalar summary metrics and bin-level stats.
    """
    if not confidences or len(confidences) != len(labels):
        raise ValueError("Confidences and labels must be non-empty and of equal length.")

    n = len(confidences)
    bin_width = 1.0 / num_bins
    bins_data: List[ReliabilityBin] = []

    total_ece = 0.0
    max_gap = 0.0
    brier_sum = 0.0

    for i in range(num_bins):
        lower = i * bin_width
        upper = (i + 1) * bin_width

        # Collect items in bin [lower, upper) — last bin is inclusive of 1.0
        bin_confs = []
        bin_correct = 0

        for conf, y in zip(confidences, labels):
            in_bin = (lower <= conf < upper) if i < num_bins - 1 else (lower <= conf <= upper)
            if in_bin:
                bin_confs.append(conf)
                if y == 1:
                    bin_correct += 1

        count = len(bin_confs)
        if count > 0:
            mean_conf = sum(bin_confs) / count
            acc = bin_correct / count
            gap = abs(acc - mean_conf)
            total_ece += (count / n) * gap
            if gap > max_gap:
                max_gap = gap
        else:
            mean_conf = (lower + upper) / 2.0
            acc = 0.0
            gap = 0.0

        bins_data.append(
            ReliabilityBin(
                bin_index=i + 1,
                bin_lower=lower,
                bin_upper=upper,
                sample_count=count,
                mean_confidence=mean_conf,
                accuracy=acc,
                calibration_gap=gap,
            )
        )

    for conf, y in zip(confidences, labels):
        brier_sum += (conf - float(y)) ** 2

    brier_score = brier_sum / n

    return CalibrationReport(
        sample_count=n,
        num_bins=num_bins,
        ece=round(total_ece, 4),
        mce=round(max_gap, 4),
        brier_score=round(brier_score, 4),
        bins=bins_data,
        platt_params={"a": a, "b": b},
    )
