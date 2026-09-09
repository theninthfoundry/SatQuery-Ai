"""
tests/test_pure_functions.py

Covers the logic that has zero external dependencies (no rasterio/torch
needed), so `pytest tests/test_pure_functions.py` works even before the
full geospatial/ML stack is installed -- useful as a fast CI smoke gate.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.geospatial.engine import auto_utm_epsg, pixel_to_geo, denormalize_bbox
from backend.evidence.contract import compute_reliability, gsd_rating, ProvenanceTracer
from backend.agent.router import classify_intent
from backend.agent.tool_registry import TaskType
from backend.models.changenet.model import classical_change_fallback, otsu_threshold


def test_auto_utm_epsg_northern_hemisphere():
    # Ahmedabad, India ~ 72.57E, 23.02N -> UTM zone 43N -> EPSG:32643
    assert auto_utm_epsg(72.5714, 23.0225) == 32643


def test_auto_utm_epsg_southern_hemisphere():
    # Sydney ~ 151.2E, -33.8S -> UTM zone 56S -> EPSG:32756
    assert auto_utm_epsg(151.2, -33.8) == 32756


def test_pixel_to_geo_identity_transform():
    # transform = (a, b, c, d, e, f): a=1,e=-1 pixel size, c,f = origin
    transform = (1.0, 0.0, 100.0, 0.0, -1.0, 200.0)
    x, y = pixel_to_geo(transform, col=10, row=5)
    assert x == 110.0
    assert y == 195.0


def test_denormalize_bbox_scale_1000():
    bbox = [100, 200, 300, 400]  # in 0-1000 scale
    out = denormalize_bbox(bbox, width=1000, height=1000)
    assert out == [100.0, 200.0, 300.0, 400.0]


def test_gsd_rating_monotonic():
    fine = gsd_rating(2.0, "grounding")
    coarse = gsd_rating(50.0, "grounding")
    assert fine > coarse
    assert 0.0 <= coarse <= 1.0
    assert 0.0 <= fine <= 1.0


def test_compute_reliability_fallback_penalty():
    score_real, _ = compute_reliability(0.9, 1.0, 1.0, fallback_used=False)
    score_fallback, factors = compute_reliability(0.9, 1.0, 1.0, fallback_used=True)
    assert score_fallback < score_real
    assert factors["fallback_penalty"] > 0


def test_classify_intent_change_vqa():
    result = classify_intent("Has built-up area increased between these dates?", image_count=2)
    assert result.task == TaskType.CHANGE_VQA


def test_classify_intent_grounding_extracts_referring_expression():
    result = classify_intent("Highlight the water reservoir in this image", image_count=1)
    assert result.task == TaskType.GROUNDING
    assert "water reservoir" in result.referring_expression


def test_classify_intent_fusion():
    result = classify_intent("Use the optical and SAR images together to find water", image_count=2)
    assert result.task == TaskType.FUSION_OPTICAL_SAR


def test_classical_change_fallback_detects_synthetic_change():
    h, w = 64, 64
    t1 = np.random.default_rng(0).integers(1000, 1500, (4, h, w)).astype(np.float32)
    t2 = t1.copy()
    t2[:, 10:30, 10:30] += 2000  # inject a clear change block
    probs = classical_change_fallback(t1, t2)
    assert probs.shape == (h, w)
    assert probs[15:25, 15:25].mean() > probs[40:50, 40:50].mean()


def test_otsu_threshold_separates_bimodal():
    low = np.random.default_rng(1).normal(0.1, 0.03, 5000).clip(0, 1)
    high = np.random.default_rng(2).normal(0.8, 0.03, 500).clip(0, 1)
    probs = np.concatenate([low, high])
    t = otsu_threshold(probs)
    assert 0.2 < t < 0.7


def test_provenance_tracer_records_timing():
    tracer = ProvenanceTracer()
    with tracer.timed("dummy_step"):
        pass
    steps = tracer.steps
    assert len(steps) == 1
    assert steps[0]["tool"] == "dummy_step"
    assert steps[0]["duration_ms"] >= 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
