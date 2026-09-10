"""Unit tests for DOFA multimodal adapter and cross-modal corroboration."""

import pytest
from pathlib import Path
from backend.models.dofa.adapter import DOFAAdapter
from tests.fixtures.synthetic_optical_sar import create_synthetic_optical_sar_pair


def test_dofa_adapter_feature_extraction(tmp_path: Path):
    opt_p, sar_p = create_synthetic_optical_sar_pair(tmp_path, width=64, height=64)

    adapter = DOFAAdapter()
    assert adapter.name == "dofa_foundation"
    assert "cross_modal_corroboration" in adapter.capabilities

    # Extract Optical
    opt_feats = adapter.extract_optical_features(opt_p)
    assert opt_feats["sensor"] == "optical"
    assert opt_feats["band_count"] == 3
    assert len(opt_feats["mean_spectral"]) == 3

    # Extract SAR
    sar_feats = adapter.extract_sar_features(sar_p)
    assert sar_feats["sensor"] == "sar"
    assert "mean_sigma0_db" in sar_feats
    assert sar_feats["mean_sigma0_db"] < 0.0


def test_dofa_cross_modal_corroboration(tmp_path: Path):
    opt_p, sar_p = create_synthetic_optical_sar_pair(tmp_path, width=64, height=64)

    adapter = DOFAAdapter()
    result = adapter.fuse_and_corroborate(opt_p, sar_p)

    assert "corroboration_score" in result
    assert 0.0 <= result["corroboration_score"] <= 1.0
    assert "joint_claim" in result
    assert len(result["joint_claim"]) > 0
