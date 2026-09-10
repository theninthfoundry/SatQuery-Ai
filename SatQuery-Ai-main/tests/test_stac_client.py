import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from backend.core.observation import Sensor
from backend.core.observation import hash_asset_bytes
from backend.integrations.stac_client import (
    StacClientError,
    StacSearchParams,
    UNHASHED_SENTINEL,
    finalize_with_asset_hash,
    is_hash_finalized,
    require_finalized,
    search,
)


# A realistic shape for a Copernicus Data Space Ecosystem STAC item —
# field names/nesting match the actual CDSE STAC API, trimmed to what
# the parser needs.
REALISTIC_STAC_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": "S2B_MSIL2A_20250601T045659_N0511_R119_T43QFV_20250601T083112",
            "collection": "sentinel-2-l2a",
            "bbox": [78.30, 17.20, 79.30, 18.20],
            "properties": {
                "datetime": "2025-06-01T04:56:59Z",
                "platform": "sentinel-2b",
                "s2:product_type": "S2MSI2A",
                "processing:level": "L2A",
                "eo:cloud_cover": 4.2,
                "proj:epsg": 32643,
                "gsd": 10.0,
            },
            "assets": {
                "B03": {"href": "https://zipper.dataspace.copernicus.eu/.../B03_10m.jp2"},
                "B11": {"href": "https://zipper.dataspace.copernicus.eu/.../B11_20m.jp2"},
            },
            "links": [
                {"rel": "self", "href": "https://catalogue.dataspace.copernicus.eu/stac/collections/sentinel-2-l2a/items/S2B_MSIL2A_20250601T045659"},
            ],
        }
    ],
}


def fake_http_post(url, body):
    assert "collections" in body
    assert "bbox" in body
    return REALISTIC_STAC_RESPONSE


def test_search_parses_real_shaped_response():
    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(78.30, 17.20, 79.30, 18.20),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)),
        max_cloud_cover=20,
    )
    results = search(params, fake_http_post)
    assert len(results) == 1
    obs = results[0]

    assert obs.observation_id.startswith("S2B_MSIL2A")
    assert obs.sensor == Sensor.SENTINEL_2_L2A
    assert obs.crs == "EPSG:32643"
    assert obs.gsd == 10.0
    assert obs.cloud_fraction == pytest.approx(0.042) if hasattr(pytest, "approx") else True
    assert "B03" in obs.assets
    assert obs.timestamp.year == 2025 and obs.timestamp.month == 6


def test_unhashed_observation_is_not_finalized():
    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(78.30, 17.20, 79.30, 18.20),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)),
    )
    obs = search(params, fake_http_post)[0]
    assert obs.source_hash == UNHASHED_SENTINEL
    assert not is_hash_finalized(obs)

    with pytest.raises(StacClientError):
        require_finalized(obs)


def test_finalize_with_real_hash_then_require_finalized_passes():
    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(78.30, 17.20, 79.30, 18.20),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)),
    )
    obs = search(params, fake_http_post)[0]
    real_hash = hash_asset_bytes(b"pretend these are the real downloaded B03 bytes")
    finalized = finalize_with_asset_hash(obs, real_hash)

    assert is_hash_finalized(finalized)
    assert require_finalized(finalized) is finalized
    # original observation is untouched (immutability)
    assert obs.source_hash == UNHASHED_SENTINEL


def test_finalize_rejects_fake_hash():
    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(78.30, 17.20, 79.30, 18.20),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)),
    )
    obs = search(params, fake_http_post)[0]
    with pytest.raises(StacClientError):
        finalize_with_asset_hash(obs, "not-a-real-hash")
    with pytest.raises(StacClientError):
        finalize_with_asset_hash(obs, UNHASHED_SENTINEL)  # can't "finalize" with the sentinel itself


def test_malformed_response_raises_clear_error():
    def bad_http_post(url, body):
        return {"features": "not-a-list"}

    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(0, 0, 1, 1),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)),
    )
    with pytest.raises(StacClientError):
        search(params, bad_http_post)


def test_item_missing_assets_raises():
    def http_post_no_assets(url, body):
        item = dict(REALISTIC_STAC_RESPONSE["features"][0])
        item["assets"] = {}
        return {"type": "FeatureCollection", "features": [item]}

    params = StacSearchParams(
        collections=["sentinel-2-l2a"],
        bbox=(0, 0, 1, 1),
        datetime_range=(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)),
    )
    with pytest.raises(StacClientError):
        search(params, http_post_no_assets)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
