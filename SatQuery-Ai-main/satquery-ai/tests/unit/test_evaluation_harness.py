"""Unit tests for Benchmark Evaluation Harness."""

from backend.evaluation.harness import benchmark_harness


def test_individual_benchmark_metrics():
    # 1. RSVQA
    rsvqa = benchmark_harness.evaluate_rsvqa(sample_count=20)
    assert rsvqa.primary_metric_value > 70.0
    assert "bleu_4" in rsvqa.detailed_metrics

    # 2. Grounding
    grounding = benchmark_harness.evaluate_grounding(sample_count=20)
    assert grounding.primary_metric_value > 60.0
    assert "mean_iou_pct" in grounding.detailed_metrics

    # 3. CDVQA
    cdvqa = benchmark_harness.evaluate_cdvqa(sample_count=20)
    assert cdvqa.primary_metric_value > 70.0
    assert "f1_score_pct" in cdvqa.detailed_metrics

    # 4. BigEarthNet
    ben = benchmark_harness.evaluate_bigearthnet_corroboration(sample_count=20)
    assert ben.primary_metric_value > 80.0
    assert "corroboration_agreement_pct" in ben.detailed_metrics


def test_full_benchmark_suite_execution():
    suite_res = benchmark_harness.run_all()
    assert "timestamp" in suite_res
    assert len(suite_res["benchmarks"]) == 5
    assert "calibration_report" in suite_res
    assert "markdown_report" in suite_res
    assert "| **RSVQA-HR / VRSBench** |" in suite_res["markdown_report"]
    assert "Confidence Probability Calibration (Platt / ECE)" in suite_res["markdown_report"]
