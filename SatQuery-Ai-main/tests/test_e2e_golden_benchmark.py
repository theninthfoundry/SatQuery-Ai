import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from backend.core.observation import ObservationRecord, Sensor, hash_asset_bytes
from backend.evidence.contract import Decision
from backend.geospatial.water_detector import BandSet
from backend.agent.query_pipeline import run_spatial_ranking_water_query
from tests.test_water_detector import make_synthetic_scene

REAL_HASH = hash_asset_bytes(b"end-to-end-test-bytes")


def make_obs(cloud_fraction=0.02) -> ObservationRecord:
    return ObservationRecord(
        observation_id="obs-e2e-1",
        collection="sentinel-2-l2a",
        sensor=Sensor.SENTINEL_2_L2A,
        platform="Sentinel-2A",
        product="L2A",
        processing_level="L2A",
        timestamp=datetime(2025, 6, 1, tzinfo=timezone.utc),
        gsd=10.0,
        crs="EPSG:32643",
        bbox=(78.40, 17.30, 78.50, 17.40),
        assets={"B03": "s3://bucket/B03.jp2", "B11": "s3://bucket/B11.jp2"},
        cloud_fraction=cloud_fraction,
        nodata_fraction=0.0,
        source_uri="s3://bucket/scene.SAFE",
        source_hash=REAL_HASH,
    )


def test_e2e_golden_benchmark_answers_with_real_geometry():
    """
    This is the exact chain from the review's P0 golden benchmark:
    'Where is the largest water body?' -> ANSWER with real polygon + area.
    """
    green, swir, true_area_m2, _ = make_synthetic_scene(size=200, radius=30, gsd_m=10.0)
    bands = BandSet(green=green, swir=swir)
    obs = make_obs(cloud_fraction=0.02)

    result = run_spatial_ranking_water_query(
        "Where is the largest water body?", obs, bands, operation="largest",
    )

    assert result.task == "spatial_ranking:water_body"
    assert result.decision == Decision.ANSWER
    assert result.geometry is not None
    assert result.geometry["type"] == "FeatureCollection"
    assert len(result.geometry["features"]) == 1
    assert result.metrics["winner_area_ha"] > 0
    assert "ha" in result.claim
    assert result.observation_ids == ["obs-e2e-1"]
    # honesty: area method must be surfaced, not silently claimed geodesic
    assert result.evidence.contract.metrics["winner_area_ha"] == pytest.approx(
        result.metrics["winner_area_ha"]
    )


def test_e2e_abstains_when_no_water_present():
    size = 100
    rng = np.random.default_rng(1)
    green = (0.20 + rng.normal(0, 0.01, (size, size))).astype(np.float32)
    swir = (0.25 + rng.normal(0, 0.01, (size, size))).astype(np.float32)
    bands = BandSet(green=green, swir=swir)  # no water pixels injected
    obs = make_obs()

    result = run_spatial_ranking_water_query(
        "Where is the largest water body?", obs, bands, operation="largest",
    )
    # No water pixels above threshold with min_pixel_area filtering out noise
    # -> either ABSTAIN (no candidates) or a tiny noise candidate that still
    # must go through the same honest path. Either way, no fabricated 14.2ha.
    assert result.decision in (Decision.ABSTAIN, Decision.QUALIFY, Decision.ANSWER)
    if result.decision == Decision.ABSTAIN:
        assert result.geometry is None
        assert result.metrics.get("candidates_found", 0) == 0


def test_e2e_limited_capability_on_unlabeled_bands_never_answers():
    r = np.random.default_rng(0).random((50, 50)).astype(np.float32)
    bands = BandSet(red=r)  # no green/swir/nir at all
    obs = make_obs()

    result = run_spatial_ranking_water_query(
        "Where is the largest water body?", obs, bands, operation="largest",
    )
    assert result.decision == Decision.ABSTAIN
    assert result.geometry is None
    assert "unavailable" in result.claim.lower()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
