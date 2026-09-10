"""Unit tests for EvidenceGraph and EvidenceGate."""

import pytest
from backend.evidence import (
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
    EvidenceGate,
    GateDecision,
)


def test_evidence_gate_refusal_on_misregistration():
    gate = EvidenceGate()
    # Registration quality below 0.50 threshold
    res = gate.evaluate(
        claim_description="Urban change test",
        registration_quality=0.35,
        spatial_overlap=0.80,
    )
    assert res.decision == GateDecision.ABSTAIN
    assert any("co-registration" in r.lower() for r in res.reasons)


def test_evidence_gate_refusal_on_cloud():
    gate = EvidenceGate()
    # Cloud contamination 75% without SAR corroboration
    res = gate.evaluate(
        claim_description="Urban change test",
        registration_quality=0.90,
        spatial_overlap=0.90,
        cloud_fraction=0.75,
        has_cross_modal_corroboration=False,
    )
    assert res.decision == GateDecision.ABSTAIN
    assert any("cloud" in r.lower() for r in res.reasons)


def test_evidence_gate_qualification_on_moderate_cloud():
    gate = EvidenceGate()
    # Cloud contamination 40% -> Qualified answer
    res = gate.evaluate(
        claim_description="Urban change test",
        registration_quality=0.90,
        spatial_overlap=0.90,
        cloud_fraction=0.40,
    )
    assert res.decision == GateDecision.QUALIFY
    assert len(res.caveats) > 0


def test_evidence_gate_answer_on_clean_data():
    gate = EvidenceGate()
    res = gate.evaluate(
        claim_description="Urban change test",
        registration_quality=0.95,
        spatial_overlap=0.95,
        cloud_fraction=0.05,
    )
    assert res.decision == GateDecision.ANSWER
    assert len(res.caveats) == 0


def test_evidence_graph_lineage_trace():
    graph = EvidenceGraph()

    n1 = EvidenceNode(id="obs_1", node_type=EvidenceNodeType.ASSET_OBSERVATION, source="Sentinel-2", description="L2A image", confidence=0.98)
    n2 = EvidenceNode(id="det_1", node_type=EvidenceNodeType.MODEL_DETECTION, source="ChangeNet", description="Detected changed mask", confidence=0.91, depends_on=["obs_1"])
    n3 = EvidenceNode(id="claim_1", node_type=EvidenceNodeType.SYNTHESIZED_CLAIM, source="AgentSynthesizer", description="Urban increased by 14%", confidence=0.90, depends_on=["det_1"])

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    trace = graph.trace_claim("claim_1")
    trace_ids = [n.id for n in trace]

    assert "obs_1" in trace_ids
    assert "det_1" in trace_ids
    assert "claim_1" in trace_ids
