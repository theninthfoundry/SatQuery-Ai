"""Unit tests for TemporalReasoningEngine, SpatialFusionEngine, SensorDisagreementEngine, SemanticChangeClassifier."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from backend.engines import (
    TemporalReasoningEngine,
    TemporalObservation,
    SpatialFusionEngine,
    SensorDisagreementEngine,
    SemanticChangeClassifier,
    ChangeCategory,
)


def test_spatial_fusion_agreement():
    opt_mask = np.zeros((100, 100), dtype=bool)
    sar_mask = np.zeros((100, 100), dtype=bool)

    # Overlapping 30x30 square
    opt_mask[10:40, 10:40] = True
    sar_mask[10:40, 10:40] = True

    # SAR-only 10x10 patch
    sar_mask[60:70, 60:70] = True

    engine = SpatialFusionEngine()
    res = engine.fuse_binary_detections(opt_mask, sar_mask, pixel_size_meters=10.0)

    assert res.agreement_pixels == 900
    assert res.sar_only_pixels == 100
    assert res.optical_only_pixels == 0
    assert res.iou == 0.90  # 900 / (900 + 100)
    assert res.agreement_area_m2 == 90000.0  # 900 * 100 m²


def test_sensor_disagreement_diagnosis():
    opt_mask = np.zeros((100, 100), dtype=bool)
    sar_mask = np.zeros((100, 100), dtype=bool)

    # Optical detects water, SAR does not (simulating wind chop)
    opt_mask[20:60, 20:60] = True

    diag = SensorDisagreementEngine()
    diagnosis = diag.diagnose_water_disagreement(opt_mask, sar_mask)

    assert diagnosis.total_disagreement_pixels > 0
    assert diagnosis.optical_only_fraction == 1.0
    assert "optical sensors detected water" in diagnosis.scientific_explanation.lower()


def test_semantic_change_classification():
    change_mask = np.zeros((100, 100), dtype=bool)
    change_mask[10:50, 10:50] = True  # 1600 pixels changed

    delta_ndbi = np.zeros((100, 100), dtype=np.float32)
    delta_ndbi[10:50, 10:50] = 0.25  # Increased built-up index

    delta_ndvi = np.zeros((100, 100), dtype=np.float32)
    delta_ndvi[10:50, 10:50] = -0.30  # Decreased vegetation index

    classifier = SemanticChangeClassifier()
    res = classifier.classify_changes(change_mask, delta_ndvi=delta_ndvi, delta_ndbi=delta_ndbi, pixel_size_meters=10.0)

    assert res.changed_pixels == 1600
    assert res.dominant_transition == ChangeCategory.NEW_URBAN_BUILTUP
    assert any(b.category == ChangeCategory.NEW_URBAN_BUILTUP for b in res.breakdown)


def test_temporal_trajectory_analysis():
    t0 = datetime(2023, 1, 1)
    obs = [
        TemporalObservation(asset_id="1", timestamp=t0, metric_name="built_up_ha", value=100.0),
        TemporalObservation(asset_id="2", timestamp=t0 + timedelta(days=180), metric_name="built_up_ha", value=120.0),
        TemporalObservation(asset_id="3", timestamp=t0 + timedelta(days=365), metric_name="built_up_ha", value=150.0),
    ]

    engine = TemporalReasoningEngine()
    traj = engine.analyze_trajectory(obs, phenomenon_type="built_up")

    assert traj.start_value == 100.0
    assert traj.end_value == 150.0
    assert traj.absolute_change == 50.0
    assert traj.percentage_change == 50.0
    assert traj.monotonic
