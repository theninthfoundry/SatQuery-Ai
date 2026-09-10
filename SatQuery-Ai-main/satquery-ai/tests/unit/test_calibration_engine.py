"""Unit tests for formal confidence calibration, Platt scaling, ECE, and reliability diagrams."""

import pytest
from backend.evidence.calibration import (
    sigmoid,
    platt_scale,
    fit_platt_scaling,
    compute_calibration_metrics,
    CalibrationReport,
)
from backend.evidence.confidence import (
    compute_vqa_confidence,
    compute_multimodal_confidence,
    ConfidenceScore,
)
from backend.evaluation.harness import benchmark_harness


def test_sigmoid_math():
    assert sigmoid(0.0) == 0.5
    assert sigmoid(100.0) == 1.0
    assert sigmoid(-100.0) < 1e-10


def test_platt_scaling_bounds():
    # Test typical remote sensing score range [0.0, 1.0]
    p_low = platt_scale(0.1)
    p_mid = platt_scale(0.5)
    p_high = platt_scale(0.95)

    assert 0.0 < p_low < p_mid < p_high < 1.0
    assert 0.01 <= p_low <= 0.99
    assert 0.01 <= p_high <= 0.99


def test_fit_platt_scaling():
    raw_scores = [0.9, 0.8, 0.7, 0.4, 0.3, 0.2]
    labels = [1, 1, 1, 0, 0, 0]

    a, b = fit_platt_scaling(raw_scores, labels, learning_rate=0.1, max_epochs=100)
    assert isinstance(a, float)
    assert isinstance(b, float)
    # Slope a should be positive when higher scores correlate with correctness (label=1)
    assert a > 0


def test_compute_calibration_metrics_ece():
    # Perfectly calibrated case
    confs = [0.1, 0.2, 0.3, 0.8, 0.9, 0.9]
    labels = [0, 0, 0, 1, 1, 1]

    report = compute_calibration_metrics(confs, labels, num_bins=5)
    assert isinstance(report, CalibrationReport)
    assert report.sample_count == 6
    assert report.num_bins == 5
    assert 0.0 <= report.ece <= 1.0
    assert 0.0 <= report.mce <= 1.0
    assert 0.0 <= report.brier_score <= 1.0
    assert len(report.bins) == 5

    rep_dict = report.to_dict()
    assert "expected_calibration_error_pct" in rep_dict
    assert "reliability_diagram_bins" in rep_dict
    assert "brier_score" in rep_dict


def test_compute_vqa_and_multimodal_confidence_calibration():
    vqa_conf = compute_vqa_confidence(model_confidence=0.85, x_res=10.0, y_res=10.0)
    assert isinstance(vqa_conf, ConfidenceScore)
    assert vqa_conf.calibrated_probability is not None
    assert 0.0 <= vqa_conf.calibrated_probability <= 1.0

    multi_conf = compute_multimodal_confidence(
        model_confidence=0.80, registration_quality=0.90, sar_agreement=0.85
    )
    assert isinstance(multi_conf, ConfidenceScore)
    assert multi_conf.calibrated_probability is not None
    assert 0.0 <= multi_conf.calibrated_probability <= 1.0

    d = multi_conf.to_dict()
    assert "calibrated_probability" in d
    assert "overall" in d


def test_harness_calibration_evaluation():
    metric_res, cal_report = benchmark_harness.evaluate_confidence_calibration()
    assert metric_res.benchmark_name == "Confidence Probability Calibration (Platt / ECE)"
    assert metric_res.sample_count == 20
    assert "ece_pct" in metric_res.detailed_metrics
    assert "brier_score" in metric_res.detailed_metrics

    full_results = benchmark_harness.run_all()
    assert "calibration_report" in full_results
    assert "expected_calibration_error_pct" in full_results["calibration_report"]
