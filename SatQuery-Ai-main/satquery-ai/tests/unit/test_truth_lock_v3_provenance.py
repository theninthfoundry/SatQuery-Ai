"""Unit tests for TRUTH LOCK v3 — Optical-SAR spatial overlap, honest abstention, and measured reliability."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from backend.pipelines.optical_sar import validate_cross_modal_pair, run_optical_sar_pipeline
from backend.models_db import ImageRecord
from backend.geospatial.target_analyzers import (
    WaterBodyTargetAnalyzer,
    BuiltUpTargetAnalyzer,
    VegetationTargetAnalyzer,
    TargetAnalysisResult,
)
from backend.engines.spatial_ranking import SpatialRankingEngine


def test_optical_sar_disjoint_spatial_overlap_abstains():
    """Verify that images with disjoint bounds strictly return iou=0.0 and fail fast with ABSTAIN."""
    # Create disjoint bounding boxes
    opt_row = MagicMock(spec=ImageRecord)
    opt_row.id = "img_opt_1"
    opt_row.filename = "optical_hyd.tif"
    opt_row.modality = "optical"
    opt_row.bounds = {"min_lon": 78.0, "min_lat": 17.0, "max_lon": 78.5, "max_lat": 17.5}

    sar_row = MagicMock(spec=ImageRecord)
    sar_row.id = "img_sar_1"
    sar_row.filename = "sar_kolkata.tif"
    sar_row.modality = "sar"
    sar_row.bounds = {"min_lon": 88.0, "min_lat": 22.0, "max_lon": 88.5, "max_lat": 22.5}

    is_valid, iou_score, warnings = validate_cross_modal_pair(opt_row, sar_row)

    assert is_valid is False
    assert iou_score == 0.0
    assert any("no geographic overlap" in w.lower() for w in warnings)


def test_optical_sar_missing_bounds_fails():
    """Verify that missing or None bounds do NOT fall back to 0.92; they must fail validation."""
    opt_row = MagicMock(spec=ImageRecord)
    opt_row.bounds = None
    opt_row.modality = "optical"

    sar_row = MagicMock(spec=ImageRecord)
    sar_row.bounds = {"min_lon": 78.0, "min_lat": 17.0, "max_lon": 78.5, "max_lat": 17.5}
    sar_row.modality = "sar"

    is_valid, iou_score, warnings = validate_cross_modal_pair(opt_row, sar_row)

    assert is_valid is False
    assert iou_score == 0.0


def test_optical_sar_overlapping_pair_calculates_real_iou():
    """Verify that overlapping bounding boxes calculate exact geometric intersection over union."""
    opt_row = MagicMock(spec=ImageRecord)
    opt_row.modality = "optical"
    opt_row.bounds = {"min_lon": 0.0, "min_lat": 0.0, "max_lon": 10.0, "max_lat": 10.0}

    sar_row = MagicMock(spec=ImageRecord)
    sar_row.modality = "sar"
    sar_row.bounds = {"min_lon": 5.0, "min_lat": 0.0, "max_lon": 15.0, "max_lat": 10.0}

    is_valid, iou_score, warnings = validate_cross_modal_pair(opt_row, sar_row)

    # Overlap: 5 to 10 x 0 to 10 = 50 area. Union: 100 + 100 - 50 = 150 area. IoU = 50/150 = 0.3333
    assert is_valid is True
    assert 0.33 <= iou_score <= 0.34


def test_target_analyzers_measured_reliability_schema():
    """Verify TargetAnalysisResult contains all measured reliability factors without synthetic defaults."""
    res = TargetAnalysisResult(
        image_id="test_img",
        target_type="water_body",
        candidates=[],
        total_detected_area_ha=0.0,
        mean_uncertainty_ha=0.0,
        processing_time_sec=0.05,
        index_name="MNDWI",
        threshold_used=0.0,
        is_empty=True,
        valid_pixel_coverage=0.98,
        cloud_freedom=0.95,
        resolution_suitability=1.0,
        spectral_distinctiveness=0.85,
        geometry_validity=1.0,
        reliability_score=0.7913,
        reliability_factors={
            "valid_pixel_coverage": 0.98,
            "cloud_freedom": 0.95,
            "resolution_suitability": 1.0,
            "spectral_distinctiveness": 0.85,
            "geometry_validity": 1.0,
        },
    )

    assert res.valid_pixel_coverage == 0.98
    assert res.cloud_freedom == 0.95
    assert res.resolution_suitability == 1.0
    assert res.spectral_distinctiveness == 0.85
    assert res.geometry_validity == 1.0
    assert 0.79 <= res.reliability_score <= 0.80
    assert len(res.reliability_factors) == 5
