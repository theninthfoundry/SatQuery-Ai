"""
Canonical query orchestrator — enforces audit section 3's invariant:

    "There must be exactly one path from a user question to an
    analytical result."

This wires the pieces built so far into the P0 golden benchmark chain:

    "Where is the largest water body?"
        -> SPATIAL_RANKING
        -> ACTIVE OBSERVATION
        -> MNDWI (water_detector.detect_water_bodies)
        -> WATER MASK / COMPONENTS / POLYGONS (inside water_detector)
        -> LARGEST (water_detector.rank_candidates)
        -> EvidenceContract
        -> EvidenceGate
        -> CanonicalAnalysisResult

Map, chat, evidence panel, and report are all expected to render from
the CanonicalAnalysisResult this function returns — never recompute
independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from backend.core.observation import ObservationRecord
from backend.evidence.contract import (
    Decision,
    EvidenceContract,
    EvidenceFactors,
    GateResult,
    evidence_gate,
)
from backend.geospatial.water_detector import (
    BandSet,
    Capability,
    WaterDetectionResult,
    detect_water_bodies,
    rank_candidates,
)


class QueryPipelineError(ValueError):
    pass


@dataclass
class CanonicalAnalysisResult:
    """
    The one object every surface (map/chat/evidence/report) must render.
    """
    query: str
    task: str
    decision: Decision
    claim: str
    geometry: Optional[dict[str, Any]]   # GeoJSON, or None on ABSTAIN
    metrics: dict[str, Any]
    evidence: GateResult
    observation_ids: list[str]


def _registration_quality_from_cloud_fraction(cloud_fraction: Optional[float]) -> Optional[float]:
    """Simple, inspectable proxy — not a learned/opaque score."""
    if cloud_fraction is None:
        return None
    return max(0.0, 1.0 - cloud_fraction)


def run_spatial_ranking_water_query(
    query: str,
    observation: ObservationRecord,
    bands: BandSet,
    *,
    operation: str = "largest",
    gsd_m: Optional[float] = None,
) -> CanonicalAnalysisResult:
    """
    The single, mandatory path for water-body spatial-ranking queries.
    No frontend shortcut, no alternative pipeline may bypass this.
    """
    if operation not in ("largest", "smallest"):
        raise QueryPipelineError("operation must be 'largest' or 'smallest'")

    gsd = gsd_m if gsd_m is not None else observation.gsd

    detection: WaterDetectionResult = detect_water_bodies(bands, gsd_m=gsd)
    ranked = rank_candidates(detection, operation=operation)

    factors = EvidenceFactors(
        registration_quality=_registration_quality_from_cloud_fraction(observation.cloud_fraction),
        gsd_resolution_rating=min(1.0, 10.0 / gsd) if gsd > 0 else None,
        cloud_contamination=observation.cloud_fraction,
        band_availability=1.0 if detection.capability == Capability.FULL else 0.0,
        data_provenance_complete=True,
    )

    if detection.capability != Capability.FULL or not ranked:
        claim = (
            f"No water bodies could be confidently detected in observation "
            f"{observation.observation_id}."
            if detection.capability == Capability.FULL
            else "Water detection unavailable: required spectral bands not present."
        )
        contract = EvidenceContract(
            id=f"water-{observation.observation_id}",
            task="spatial_ranking:water_body",
            model_ids=[],
            is_real_weights=False,
            fallback_used=False,
            observation_ids=[observation.observation_id],
            claim=claim,
            spatial_evidence=None,
            metrics={"candidates_found": 0},
            factors=factors,
            limitations=list(detection.limitation_notes),
        )
        gate_result = evidence_gate(contract, has_spatial_evidence_required=True)
        return CanonicalAnalysisResult(
            query=query, task="spatial_ranking:water_body",
            decision=gate_result.decision, claim=claim, geometry=None,
            metrics={"candidates_found": 0}, evidence=gate_result,
            observation_ids=[observation.observation_id],
        )

    winner = ranked[0]
    geometry = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "candidate_id": winner.candidate_id,
                "area_m2": winner.area_m2,
                "area_ha": winner.area_ha,
                "area_method": winner.area_method,
            },
            "geometry": {
                "type": "Polygon",
                # NOTE: contour_px are pixel coordinates here; in production
                # these must be run through the real affine transform before
                # being placed in a GeoJSON FeatureCollection with lon/lat.
                "coordinates": [winner.contour_px],
            },
        }],
    }

    claim = (
        f"{operation.capitalize()} water body detected via {detection.index_used}: "
        f"{winner.area_ha:.2f} ha ({winner.area_method})."
    )

    contract = EvidenceContract(
        id=f"water-{observation.observation_id}",
        task="spatial_ranking:water_body",
        model_ids=[],
        is_real_weights=False,
        fallback_used=False,
        observation_ids=[observation.observation_id],
        claim=claim,
        spatial_evidence=geometry,
        metrics={
            "candidates_found": len(ranked),
            "winner_area_m2": winner.area_m2,
            "winner_area_ha": winner.area_ha,
            "index_used": detection.index_used,
            "threshold": detection.threshold,
        },
        factors=factors,
        limitations=list(detection.limitation_notes) + (
            ["Area is a pixel-grid approximation, not geodesic (pyproj/shapely unavailable)."]
            if winner.area_method == "pixel_grid_approx" else []
        ),
    )
    gate_result = evidence_gate(contract, has_spatial_evidence_required=True)

    return CanonicalAnalysisResult(
        query=query, task="spatial_ranking:water_body",
        decision=gate_result.decision, claim=claim,
        geometry=geometry if gate_result.decision != Decision.ABSTAIN else None,
        metrics=contract.metrics, evidence=gate_result,
        observation_ids=[observation.observation_id],
    )
