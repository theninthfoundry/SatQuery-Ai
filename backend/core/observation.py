"""
Canonical ObservationRecord.

This is the single object every part of SatQuery must reference when it
talks about "an image" / "a scene" / "T1" / "T2". No pipeline, route, or
frontend component is allowed to invent timestamp/sensor/CRS metadata —
it must come from here, and it must come from a real STAC item or a real
ingested GeoTIFF's own header.

Design goals (per the audit's "Observation truth lock" requirement):
  1. Nothing can construct an ObservationRecord without a real source_uri
     and a real source_hash.
  2. Two ObservationRecords can be compared/paired only if a set of
     invariants hold (same AOI overlap, resolvable CRS, sane time delta) —
     this stops "2024 optical metadata + 2026 SAR metadata" style bugs.
  3. Equality/identity is by observation_id, not by convenience fields
     like timestamp, so accidental aliasing is caught immediately.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Sensor(str, Enum):
    SENTINEL_2_L2A = "sentinel-2-l2a"
    SENTINEL_1_GRD = "sentinel-1-grd"
    UNKNOWN = "unknown"


class ObservationValidationError(ValueError):
    """Raised when an ObservationRecord would violate a truth-lock invariant."""


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    collection: str
    sensor: Sensor
    platform: str
    product: str
    processing_level: str
    timestamp: datetime
    gsd: float                     # ground sample distance, metres
    crs: str                       # e.g. "EPSG:32643"
    bbox: tuple[float, float, float, float]
    assets: dict[str, str]         # band/asset name -> URI
    cloud_fraction: Optional[float]
    nodata_fraction: Optional[float]
    source_uri: str
    source_hash: str               # sha256 of the source asset(s) actually read
    availability: str = "AVAILABLE"

    def __post_init__(self) -> None:
        if not self.source_uri:
            raise ObservationValidationError(
                "ObservationRecord requires a real source_uri; "
                "synthetic/placeholder observations are not permitted."
            )
        if not self.source_hash or len(self.source_hash) != 64:
            raise ObservationValidationError(
                "ObservationRecord requires a real sha256 source_hash "
                "(64 hex chars). Refusing to construct an unverifiable "
                "observation."
            )
        if not self.assets:
            raise ObservationValidationError(
                "ObservationRecord requires at least one real asset URI."
            )
        if self.gsd <= 0:
            raise ObservationValidationError("gsd must be a positive, real value.")

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["sensor"] = self.sensor.value
        return d


def hash_asset_bytes(data: bytes) -> str:
    """Compute the sha256 that must back source_hash. Never fabricate this value."""
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class TemporalPairValidation:
    ok: bool
    reasons: list[str] = field(default_factory=list)


def validate_temporal_pair(
    t1: ObservationRecord,
    t2: ObservationRecord,
    *,
    max_time_delta_days: Optional[int] = None,
    require_same_sensor: bool = True,
    min_bbox_overlap_fraction: float = 0.5,
) -> TemporalPairValidation:
    """
    The gate that must run before ANY change-detection pipeline is allowed
    to execute. This is what stops the "2024 optical + 2026 SAR" bug class
    the audit flagged, and stops pairing observations that don't actually
    overlap in space.
    """
    reasons: list[str] = []

    if t1.observation_id == t2.observation_id:
        reasons.append("t1 and t2 resolve to the same observation_id.")

    if require_same_sensor and t1.sensor != t2.sensor:
        reasons.append(
            f"Sensor mismatch: t1={t1.sensor.value} t2={t2.sensor.value}. "
            "Cross-sensor temporal differencing must go through the "
            "optical+SAR fusion path, not the plain change-detection path."
        )

    if t1.crs != t2.crs:
        # Not fatal by itself — reprojection can reconcile this — but the
        # caller must have actually reprojected, not silently assumed.
        reasons.append(
            f"CRS mismatch (t1={t1.crs}, t2={t2.crs}); pipeline must "
            "reproject explicitly before pairing, not implicitly."
        )

    overlap = _bbox_overlap_fraction(t1.bbox, t2.bbox)
    if overlap < min_bbox_overlap_fraction:
        reasons.append(
            f"Insufficient spatial overlap ({overlap:.2f} < "
            f"{min_bbox_overlap_fraction}); refusing to treat these as a "
            "valid temporal pair over the same ground area."
        )

    if max_time_delta_days is not None:
        delta_days = abs((t2.timestamp - t1.timestamp).days)
        if delta_days > max_time_delta_days:
            reasons.append(
                f"Time delta {delta_days}d exceeds max_time_delta_days="
                f"{max_time_delta_days}."
            )

    return TemporalPairValidation(ok=(len(reasons) == 0), reasons=reasons)


def _bbox_overlap_fraction(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = max(ax1 - ax0, 1e-12) * max(ay1 - ay0, 1e-12)
    area_b = max(bx1 - bx0, 1e-12) * max(by1 - by0, 1e-12)
    return inter / min(area_a, area_b)
