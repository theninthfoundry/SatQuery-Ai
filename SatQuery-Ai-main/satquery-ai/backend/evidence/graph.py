"""Directed Evidence Graph connecting claims directly to raw sensor observations.

Every assertion made by SatQuery AI is grounded in an explicit chain of evidence nodes:
Asset Observation → Perceptual Detection → Spatial Measurement → Synthesized Claim.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set


class EvidenceNodeType(str, Enum):
    """Categorization of evidence nodes in the audit graph."""
    ASSET_OBSERVATION = "asset_observation"      # Raw sensor imagery and metadata
    MODEL_DETECTION = "model_detection"          # Neural network inference output
    SPECTRAL_MEASUREMENT = "spectral_measurement" # Deterministic band index calculation
    SPATIAL_RELATION = "spatial_relation"        # Geometric overlay, intersection, or co-registration
    SYNTHESIZED_CLAIM = "synthesized_claim"      # High-level domain answer or decision


@dataclass
class EvidenceNode:
    """A verified unit of evidence with provenance and confidence attribution."""
    id: str
    node_type: EvidenceNodeType
    source: str  # Tool, model, or sensor name
    description: str
    confidence: float
    data: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON representation
    depends_on: List[str] = field(default_factory=list)  # Parent evidence node IDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "source": self.source,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "data": self.data,
            "geometry": self.geometry,
            "depends_on": self.depends_on,
        }


class EvidenceGraph:
    """Audit graph tracking the lineage of evidence supporting an answer."""

    def __init__(self, graph_id: Optional[str] = None):
        self.graph_id = graph_id or f"evg_{uuid.uuid4().hex[:10]}"
        self.nodes: Dict[str, EvidenceNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (parent_id, child_id)

    def add_node(self, node: EvidenceNode) -> str:
        """Add an evidence node to the graph and record its incoming edges."""
        self.nodes[node.id] = node
        for parent_id in node.depends_on:
            if (parent_id, node.id) not in self.edges:
                self.edges.append((parent_id, node.id))
        return node.id

    def trace_claim(self, claim_node_id: str) -> List[EvidenceNode]:
        """Backtrack from a claim node to all upstream parent evidence nodes in topological order."""
        if claim_node_id not in self.nodes:
            raise KeyError(f"Node {claim_node_id} not found in evidence graph")

        visited: Set[str] = set()
        trace: List[EvidenceNode] = []

        def dfs(nid: str):
            if nid in visited:
                return
            visited.add(nid)
            node = self.nodes.get(nid)
            if node:
                for parent_id in node.depends_on:
                    dfs(parent_id)
                trace.append(node)

        dfs(claim_node_id)
        return trace

    def compute_chain_confidence(self, claim_node_id: str) -> float:
        """Compute weakest-link (bottleneck) or joint confidence along the evidence path."""
        chain = self.trace_claim(claim_node_id)
        if not chain:
            return 0.0
        # Product of confidences with soft thresholding
        scores = [n.confidence for n in chain]
        min_score = min(scores)
        mean_score = sum(scores) / len(scores)
        # Harmonized score: 60% weakest link + 40% average
        return round(0.60 * min_score + 0.40 * mean_score, 3)

    def to_dict(self) -> Dict[str, Any]:
        """Export graph to structured JSON."""
        return {
            "graph_id": self.graph_id,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [{"from": u, "to": v} for u, v in self.edges],
        }

    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Export format optimized for frontend graph visualizers (Cytoscape / D3)."""
        elements = []
        for nid, n in self.nodes.items():
            elements.append({
                "data": {
                    "id": nid,
                    "label": n.description[:40],
                    "type": n.node_type.value,
                    "source": n.source,
                    "confidence": n.confidence,
                }
            })
        for u, v in self.edges:
            elements.append({
                "data": {
                    "id": f"e_{u}_{v}",
                    "source": u,
                    "target": v,
                }
            })
        return elements
