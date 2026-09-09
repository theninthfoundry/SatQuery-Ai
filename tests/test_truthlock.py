"""
Run with: python -m pytest tests/ -v
(or, if pytest isn't installed here, this file also runs standalone via
`python tests/test_truthlock.py` using the __main__ block at the bottom.)
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from backend.core.observation import (
    ObservationRecord,
    ObservationValidationError,
    Sensor,
    hash_asset_bytes,
    validate_temporal_pair,
)
from backend.models.registry import (
    InvalidTransitionError,
    ModelEntry,
    ModelNotReadyError,
    ModelRegistry,
    ModelStatus,
    ModelType,
)
from backend.evidence.contract import (
    EvidenceContract,
    EvidenceContractError,
    EvidenceFactors,
    EvidenceStrength,
    Decision,
    compute_evidence_strength,
    evidence_gate,
)
from backend.agent.grounding_contract import run_grounding, offline_fallback_grounding


REAL_HASH = hash_asset_bytes(b"fake-but-real-bytes-for-testing")


def make_obs(**overrides) -> ObservationRecord:
    defaults = dict(
        observation_id="obs-1",
        collection="sentinel-2-l2a",
        sensor=Sensor.SENTINEL_2_L2A,
        platform="Sentinel-2A",
        product="L2A",
        processing_level="L2A",
        timestamp=datetime(2024, 3, 14, tzinfo=timezone.utc),
        gsd=10.0,
        crs="EPSG:32643",
        bbox=(78.40, 17.30, 78.50, 17.40),
        assets={"B04": "s3://bucket/B04.jp2"},
        cloud_fraction=0.05,
        nodata_fraction=0.0,
        source_uri="s3://bucket/scene.SAFE",
        source_hash=REAL_HASH,
    )
    defaults.update(overrides)
    return ObservationRecord(**defaults)


# ---------- ObservationRecord ----------

def test_observation_rejects_missing_source_uri():
    with pytest.raises(ObservationValidationError):
        make_obs(source_uri="")


def test_observation_rejects_fake_hash():
    with pytest.raises(ObservationValidationError):
        make_obs(source_hash="not-a-real-hash")


def test_observation_rejects_no_assets():
    with pytest.raises(ObservationValidationError):
        make_obs(assets={})


def test_valid_observation_constructs():
    obs = make_obs()
    assert obs.observation_id == "obs-1"


def test_temporal_pair_rejects_sensor_mismatch():
    t1 = make_obs(observation_id="o1")
    t2 = make_obs(
        observation_id="o2",
        sensor=Sensor.SENTINEL_1_GRD,
        collection="sentinel-1-grd",
        timestamp=datetime(2026, 3, 19, tzinfo=timezone.utc),
    )
    result = validate_temporal_pair(t1, t2)
    assert not result.ok
    assert any("Sensor mismatch" in r for r in result.reasons)


def test_temporal_pair_rejects_no_overlap():
    t1 = make_obs(observation_id="o1", bbox=(0, 0, 1, 1))
    t2 = make_obs(observation_id="o2", bbox=(50, 50, 51, 51),
                   timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    result = validate_temporal_pair(t1, t2)
    assert not result.ok


def test_temporal_pair_valid():
    t1 = make_obs(observation_id="o1", timestamp=datetime(2024, 3, 14, tzinfo=timezone.utc))
    t2 = make_obs(observation_id="o2", timestamp=datetime(2026, 3, 19, tzinfo=timezone.utc))
    result = validate_temporal_pair(t1, t2, max_time_delta_days=1000)
    assert result.ok


# ---------- ModelRegistry ----------

def test_model_starts_not_ready():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))
    with pytest.raises(ModelNotReadyError):
        reg.assert_ready("geochat-7b")


def test_model_cannot_skip_states():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))
    with pytest.raises(InvalidTransitionError):
        reg.mark_verified(
            "geochat-7b",
            checkpoint_sha256=REAL_HASH,
            test_image_hash=REAL_HASH,
            test_output_hash=REAL_HASH,
        )


def test_model_becomes_ready_only_through_full_path():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))
    reg.mark_downloading("geochat-7b")
    reg.mark_installed("geochat-7b")
    reg.mark_loadable("geochat-7b")
    reg.mark_verified(
        "geochat-7b",
        checkpoint_sha256=REAL_HASH,
        test_image_hash=REAL_HASH,
        test_output_hash=REAL_HASH,
    )
    entry = reg.assert_ready("geochat-7b")
    assert entry.status == ModelStatus.READY
    assert entry.is_ready()


def test_mark_verified_rejects_fake_hash():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))
    reg.mark_downloading("geochat-7b")
    reg.mark_installed("geochat-7b")
    reg.mark_loadable("geochat-7b")
    with pytest.raises(InvalidTransitionError):
        reg.mark_verified(
            "geochat-7b",
            checkpoint_sha256="not-real",
            test_image_hash=REAL_HASH,
            test_output_hash=REAL_HASH,
        )


# ---------- Grounding fail-closed ----------

def test_grounding_fails_closed_when_model_not_ready():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))

    def fake_infer(*a, **k):
        raise AssertionError("should never be called when model isn't ready")

    result = run_grounding(reg, "geochat-7b", fake_infer)
    assert result.fallback_used is True
    assert result.execution_mode == "offline_fallback"
    assert result.boxes == []
    assert result.model_confidence is None


def test_grounding_runs_real_inference_when_ready():
    reg = ModelRegistry()
    reg.register(ModelEntry(id="geochat-7b", type=ModelType.TRAINED_MODEL, source_uri="hf://x"))
    reg.mark_downloading("geochat-7b")
    reg.mark_installed("geochat-7b")
    reg.mark_loadable("geochat-7b")
    reg.mark_verified(
        "geochat-7b",
        checkpoint_sha256=REAL_HASH,
        test_image_hash=REAL_HASH,
        test_output_hash=REAL_HASH,
    )

    def fake_infer(*a, **k):
        return [{"box": [0.1, 0.1, 0.2, 0.2]}], 0.91

    result = run_grounding(reg, "geochat-7b", fake_infer)
    assert result.fallback_used is False
    assert result.execution_mode == "model_inference"
    assert result.boxes[0]["box"] == [0.1, 0.1, 0.2, 0.2]
    assert result.checkpoint_sha256 == REAL_HASH


# ---------- EvidenceContract / Gate ----------

def test_contract_rejects_fake_confident_fallback():
    with pytest.raises(EvidenceContractError):
        EvidenceContract(
            id="e1", task="change_detection", model_ids=["changenet"],
            is_real_weights=True, fallback_used=True,
            observation_ids=["o1", "o2"], claim="x",
            spatial_evidence=None, metrics={}, factors=EvidenceFactors(),
        )


def test_contract_requires_observation_ids():
    with pytest.raises(EvidenceContractError):
        EvidenceContract(
            id="e1", task="change_detection", model_ids=[],
            is_real_weights=False, fallback_used=True,
            observation_ids=[], claim="x",
            spatial_evidence=None, metrics={}, factors=EvidenceFactors(),
        )


def test_no_evidence_abstains():
    factors = EvidenceFactors()  # everything None
    assert compute_evidence_strength(factors) == EvidenceStrength.INSUFFICIENT


def test_strong_evidence_answers():
    factors = EvidenceFactors(
        model_confidence=0.9, registration_quality=0.95,
        gsd_resolution_rating=0.9, cross_modal_agreement=0.85,
        band_availability=1.0, cloud_contamination=0.02,
    )
    contract = EvidenceContract(
        id="e1", task="water_ranking", model_ids=[],
        is_real_weights=False, fallback_used=False,
        observation_ids=["o1"], claim="Largest water body is 14.2 ha.",
        spatial_evidence={"type": "FeatureCollection", "features": []},
        metrics={"area_ha": 14.2}, factors=factors,
    )
    result = evidence_gate(contract)
    assert result.decision == Decision.ANSWER
    assert result.strength == EvidenceStrength.STRONG


def test_weak_evidence_abstains_end_to_end():
    factors = EvidenceFactors(model_confidence=0.1)
    contract = EvidenceContract(
        id="e2", task="water_ranking", model_ids=[],
        is_real_weights=False, fallback_used=False,
        observation_ids=["o1"], claim="uncertain",
        spatial_evidence=None, metrics={}, factors=factors,
    )
    result = evidence_gate(contract)
    assert result.decision == Decision.ABSTAIN


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
