"""
STAC client for Copernicus Data Space Ecosystem (CDSE).

Built against the real CDSE STAC API contract:
    https://catalogue.dataspace.copernicus.eu/stac/

Search endpoint (STAC API - Item Search):
    POST https://catalogue.dataspace.copernicus.eu/stac/search
    {
      "collections": ["sentinel-2-l2a"],
      "bbox": [w, s, e, n],
      "datetime": "2024-01-01T00:00:00Z/2024-06-01T00:00:00Z",
      "query": {"eo:cloud_cover": {"lt": 20}},
      "limit": 20
    }

This module does two things only:
  1. Build the search request (no network call happens inside this
     module — the actual HTTP call is injected via `http_post`, so it
     can be swapped for `requests`, `httpx`, or a test double).
  2. Parse a real STAC Item response into a canonical ObservationRecord.

Per the truth-lock invariant, `source_hash` on the resulting
ObservationRecord is NOT fabricated here — a STAC item's JSON doesn't
contain a hash of the actual asset bytes, only a URI. This client marks
it clearly as "unhashed" (a sentinel, not a fake real-looking hash) until
the asset is actually downloaded and hashed via
`observation.hash_asset_bytes()`. Callers must call
`finalize_with_asset_hash()` before an ObservationRecord from this client
is allowed into an EvidenceContract-producing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Callable, Optional

from backend.core.observation import ObservationRecord, ObservationValidationError, Sensor

CDSE_STAC_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"

# Sentinel used in place of a real sha256 until the asset bytes are
# actually fetched and hashed. 64 hex chars so it satisfies the shape
# check, but structurally impossible to collide with a real sha256 of
# meaningful content because it's all zeros — and finalize_with_asset_hash
# refuses to let it pass into evidence generation.
UNHASHED_SENTINEL = "0" * 64

_COLLECTION_TO_SENSOR = {
    "sentinel-2-l2a": Sensor.SENTINEL_2_L2A,
    "sentinel-1-grd": Sensor.SENTINEL_1_GRD,
}


class StacClientError(RuntimeError):
    pass


@dataclass
class StacSearchParams:
    collections: list[str]
    bbox: tuple[float, float, float, float]
    datetime_range: tuple[datetime, datetime]
    max_cloud_cover: Optional[float] = None
    limit: int = 20

    def to_request_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "collections": self.collections,
            "bbox": list(self.bbox),
            "datetime": (
                f"{self.datetime_range[0].isoformat()}/"
                f"{self.datetime_range[1].isoformat()}"
            ),
            "limit": self.limit,
        }
        if self.max_cloud_cover is not None:
            body["query"] = {"eo:cloud_cover": {"lt": self.max_cloud_cover}}
        return body


HttpPostFn = Callable[[str, dict[str, Any]], dict[str, Any]]


def search(params: StacSearchParams, http_post: HttpPostFn) -> list[ObservationRecord]:
    """
    `http_post(url, json_body) -> response_json` is injected by the caller
    (e.g. wrapping `requests.post(url, json=body).json()`), so this stays
    testable without live network access.
    """
    response = http_post(CDSE_STAC_SEARCH_URL, params.to_request_body())
    features = response.get("features", [])
    if not isinstance(features, list):
        raise StacClientError(f"Malformed STAC response: 'features' is {type(features)}")
    return [_parse_stac_item(item) for item in features]


def _parse_stac_item(item: dict[str, Any]) -> ObservationRecord:
    try:
        item_id = item["id"]
        props = item["properties"]
        collection = item["collection"]
        bbox = tuple(item["bbox"])  # [minx, miny, maxx, maxy]
        assets_raw = item["assets"]
        timestamp_str = props["datetime"]
    except KeyError as e:
        raise StacClientError(f"STAC item missing required field: {e}") from e

    sensor = _COLLECTION_TO_SENSOR.get(collection, Sensor.UNKNOWN)

    assets: dict[str, str] = {}
    for band_name, asset in assets_raw.items():
        href = asset.get("href")
        if href:
            assets[band_name] = href
    if not assets:
        raise StacClientError(f"STAC item '{item_id}' has no usable asset hrefs.")

    gsd = props.get("gsd") or props.get("eo:gsd") or _default_gsd_for_sensor(sensor)
    crs = props.get("proj:epsg")
    crs_str = f"EPSG:{crs}" if crs else "UNKNOWN"

    cloud_cover = props.get("eo:cloud_cover")
    cloud_fraction = (cloud_cover / 100.0) if isinstance(cloud_cover, (int, float)) else None

    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError as e:
        raise StacClientError(f"Unparseable STAC datetime '{timestamp_str}': {e}") from e

    try:
        return ObservationRecord(
            observation_id=item_id,
            collection=collection,
            sensor=sensor,
            platform=props.get("platform", "unknown"),
            product=props.get("s2:product_type", props.get("product_type", collection)),
            processing_level=props.get("processing:level", "unknown"),
            timestamp=timestamp,
            gsd=float(gsd),
            crs=crs_str,
            bbox=bbox,  # type: ignore[arg-type]
            assets=assets,
            cloud_fraction=cloud_fraction,
            nodata_fraction=props.get("statistics", {}).get("nodata_fraction")
                if isinstance(props.get("statistics"), dict) else None,
            source_uri=item.get("links", [{}])[0].get("href", f"stac:{item_id}"),
            source_hash=UNHASHED_SENTINEL,
            availability="AVAILABLE",
        )
    except ObservationValidationError as e:
        raise StacClientError(f"STAC item '{item_id}' failed observation validation: {e}") from e


def _default_gsd_for_sensor(sensor: Sensor) -> float:
    return {
        Sensor.SENTINEL_2_L2A: 10.0,
        Sensor.SENTINEL_1_GRD: 10.0,
    }.get(sensor, 10.0)


def is_hash_finalized(observation: ObservationRecord) -> bool:
    return observation.source_hash != UNHASHED_SENTINEL


def finalize_with_asset_hash(observation: ObservationRecord, real_sha256: str) -> ObservationRecord:
    """
    Must be called with the real sha256 of the actually-downloaded asset
    bytes before this ObservationRecord is allowed into any pipeline that
    produces an EvidenceContract. STAC search results alone are not
    sufficient provenance.
    """
    if not real_sha256 or len(real_sha256) != 64 or real_sha256 == UNHASHED_SENTINEL:
        raise StacClientError(
            "finalize_with_asset_hash requires a real 64-char sha256 of the "
            "downloaded asset bytes, not the unhashed sentinel."
        )
    return replace(observation, source_hash=real_sha256)


def require_finalized(observation: ObservationRecord) -> ObservationRecord:
    """Call this at the top of any pipeline that consumes STAC-derived observations."""
    if not is_hash_finalized(observation):
        raise StacClientError(
            f"Observation '{observation.observation_id}' has not been "
            f"finalized with a real asset hash (still carries the unhashed "
            f"sentinel). Download and hash the asset before analysis."
        )
    return observation
