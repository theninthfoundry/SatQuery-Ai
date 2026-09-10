import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from backend.core.data_class import DataClass, DataClassPolicyError, assert_production_safe
from backend.evidence.contract import EvidenceContract, EvidenceContractError, EvidenceFactors


def test_fallback_result_is_unavailable_capability():
    c = EvidenceContract(
        id="e1", task="grounding", model_ids=["geochat"],
        is_real_weights=False, fallback_used=True,
        observation_ids=["o1"], claim="no result",
        spatial_evidence=None, metrics={}, factors=EvidenceFactors(),
    )
    assert c.data_class == DataClass.UNAVAILABLE_CAPABILITY


def test_real_model_result_is_real_model():
    c = EvidenceContract(
        id="e2", task="vqa", model_ids=["geochat"],
        is_real_weights=True, fallback_used=False,
        observation_ids=["o1"], claim="answer",
        spatial_evidence=None, metrics={}, factors=EvidenceFactors(),
    )
    assert c.data_class == DataClass.REAL_MODEL


def test_deterministic_gis_result_is_deterministic_analysis():
    c = EvidenceContract(
        id="e3", task="spatial_ranking:water_body", model_ids=[],
        is_real_weights=False, fallback_used=False,
        observation_ids=["o1"], claim="14.2 ha",
        spatial_evidence={"type": "FeatureCollection", "features": []},
        metrics={}, factors=EvidenceFactors(),
    )
    assert c.data_class == DataClass.DETERMINISTIC_ANALYSIS


def test_explicit_data_class_must_be_consistent():
    with pytest.raises(EvidenceContractError):
        EvidenceContract(
            id="e4", task="vqa", model_ids=["geochat"],
            is_real_weights=False, fallback_used=False,  # not real weights...
            observation_ids=["o1"], claim="answer",
            spatial_evidence=None, metrics={}, factors=EvidenceFactors(),
            data_class=DataClass.REAL_MODEL,  # ...but claims REAL_MODEL anyway
        )


def test_production_gate_blocks_synthetic_fixture():
    with pytest.raises(DataClassPolicyError):
        assert_production_safe(DataClass.SYNTHETIC_FIXTURE, environment="production")


def test_production_gate_allows_unavailable_capability():
    # An honest abstention is allowed in production; a fabricated demo is not.
    assert_production_safe(DataClass.UNAVAILABLE_CAPABILITY, environment="production")


def test_production_gate_ignored_outside_production():
    # Fixtures are fine in test/demo environments.
    assert_production_safe(DataClass.SYNTHETIC_FIXTURE, environment="test")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
