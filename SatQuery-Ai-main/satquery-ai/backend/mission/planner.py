"""DAG-based mission planner for remote sensing workflows.

Constructs an executable Directed Acyclic Graph (DAG) of processing steps
tailored to the mission specification, available sensors, and compute constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from .parser import MissionSpec, MissionIntent, TemporalScope


class NodeType(str, Enum):
    """Types of computational and analytical operations in a mission DAG."""
    ASSET_VALIDATION = "asset_validation"
    COMPATIBILITY_CHECK = "compatibility_check"
    CO_REGISTRATION = "co_registration"
    SPECTRAL_INDEX = "spectral_index"
    SAR_PREPROCESSING = "sar_preprocessing"
    PERCEPTION_INFERENCE = "perception_inference"
    SPATIAL_RANKING = "spatial_ranking"
    SPATIAL_FUSION = "spatial_fusion"
    SEMANTIC_CHANGE = "semantic_change"
    DISAGREEMENT_ANALYSIS = "disagreement_analysis"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"


@dataclass
class MissionNode:
    """A single executable step in the mission DAG."""
    id: str
    node_type: NodeType
    name: str
    tool_or_model: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    estimated_vram_mb: int = 500
    estimated_latency_sec: float = 0.5
    critical: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "name": self.name,
            "tool_or_model": self.tool_or_model,
            "depends_on": self.depends_on,
            "estimated_vram_mb": self.estimated_vram_mb,
            "estimated_latency_sec": self.estimated_latency_sec,
            "critical": self.critical,
        }


@dataclass
class MissionDAG:
    """Directed Acyclic Graph representing the full execution plan."""
    mission_id: str
    nodes: Dict[str, MissionNode] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    total_estimated_vram_mb: int = 0
    total_estimated_latency_sec: float = 0.0

    def add_node(self, node: MissionNode):
        self.nodes[node.id] = node

    def compile(self) -> List[str]:
        """Compute valid topological execution order."""
        visited: Set[str] = set()
        temp: Set[str] = set()
        order: List[str] = []

        def visit(n_id: str):
            if n_id in temp:
                raise ValueError(f"Cycle detected in mission DAG at node: {n_id}")
            if n_id not in visited:
                temp.add(n_id)
                for dep in self.nodes[n_id].depends_on:
                    if dep in self.nodes:
                        visit(dep)
                temp.remove(n_id)
                visited.add(n_id)
                order.append(n_id)

        for node_id in self.nodes:
            if node_id not in visited:
                visit(node_id)

        self.execution_order = order
        self.total_estimated_latency_sec = sum(self.nodes[n].estimated_latency_sec for n in order)
        self.total_estimated_vram_mb = max((self.nodes[n].estimated_vram_mb for n in order), default=0)
        return self.execution_order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "node_count": len(self.nodes),
            "execution_order": self.execution_order,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "estimated_max_vram_mb": self.total_estimated_vram_mb,
            "estimated_total_latency_sec": round(self.total_estimated_latency_sec, 2),
        }


class MissionPlanner:
    """Constructs optimized MissionDAG execution plans tailored to MissionSpec."""

    def plan(
        self,
        spec: MissionSpec,
        asset_ids: List[str],
    ) -> MissionDAG:
        """Create and compile an execution DAG for the given mission specification.
        
        Args:
            spec: Parsed MissionSpec.
            asset_ids: List of available asset identifiers in context.
            
        Returns:
            Compiled MissionDAG.
        """
        dag = MissionDAG(mission_id=spec.mission_id)

        # 1. Base validation node
        val_node = MissionNode(
            id="step_0_validate_assets",
            node_type=NodeType.ASSET_VALIDATION,
            name="Asset Verification & Integrity Check",
            tool_or_model="InputSanitizer + AssetFactory",
            inputs={"asset_ids": asset_ids},
            depends_on=[],
            estimated_vram_mb=200,
            estimated_latency_sec=0.2,
        )
        dag.add_node(val_node)

        last_step = val_node.id

        # 2. Branch depending on Intent
        if spec.intent == MissionIntent.SINGLE_IMAGE_VQA:
            vqa_node = MissionNode(
                id="step_1_geochat_vqa",
                node_type=NodeType.PERCEPTION_INFERENCE,
                name="Remote Sensing Visual Question Answering",
                tool_or_model="GeoChatModelAdapter",
                inputs={"asset_id": asset_ids[0], "prompt": spec.query},
                depends_on=[val_node.id],
                estimated_vram_mb=6500,
                estimated_latency_sec=2.2,
            )
            dag.add_node(vqa_node)
            last_step = vqa_node.id

        elif spec.intent == MissionIntent.SPATIAL_RANKING:
            rank_node = MissionNode(
                id="step_1_spatial_ranking",
                node_type=NodeType.SPATIAL_RANKING,
                name="Deterministic Spatial Ranking & Geometric Extraction",
                tool_or_model="SpatialRankingEngine",
                inputs={
                    "asset_id": asset_ids[0],
                    "query": spec.query,
                    "target": "water_body" if "water" in spec.target_phenomena else "built_up",
                    "operation": "largest",
                },
                depends_on=[val_node.id],
                estimated_vram_mb=400,
                estimated_latency_sec=0.5,
            )
            dag.add_node(rank_node)
            last_step = rank_node.id

        elif spec.intent == MissionIntent.VISUAL_GROUNDING:
            ground_node = MissionNode(
                id="step_1_visual_grounding",
                node_type=NodeType.PERCEPTION_INFERENCE,
                name="Spatial Object Localization & Box Grounding",
                tool_or_model="GeoChatModelAdapter (Grounding)",
                inputs={"asset_id": asset_ids[0], "query": spec.query},
                depends_on=[val_node.id],
                estimated_vram_mb=6500,
                estimated_latency_sec=2.4,
            )
            dag.add_node(ground_node)
            last_step = ground_node.id

        elif spec.intent in [MissionIntent.TEMPORAL_CHANGE, MissionIntent.COMPOUND_INVESTIGATION]:
            # Step A: Check compatibility
            compat_node = MissionNode(
                id="step_1_check_compatibility",
                node_type=NodeType.COMPATIBILITY_CHECK,
                name="Scientific Asset Compatibility Evaluation",
                tool_or_model="CompatibilityEngine",
                inputs={"asset_1": asset_ids[0], "asset_2": asset_ids[1]},
                depends_on=[val_node.id],
                estimated_vram_mb=100,
                estimated_latency_sec=0.1,
            )
            dag.add_node(compat_node)

            # Step B: Co-registration
            reg_node = MissionNode(
                id="step_2_coregistration",
                node_type=NodeType.CO_REGISTRATION,
                name="AKAZE Sub-pixel Image Co-registration",
                tool_or_model="align_image_pairs",
                inputs={"ref_id": asset_ids[0], "target_id": asset_ids[1]},
                depends_on=[compat_node.id],
                estimated_vram_mb=800,
                estimated_latency_sec=0.8,
            )
            dag.add_node(reg_node)

            # Step C: Change Detection Inference
            change_node = MissionNode(
                id="step_3_changenet_inference",
                node_type=NodeType.PERCEPTION_INFERENCE,
                name="Bi-temporal ChangeNet Feature Discrimination",
                tool_or_model="ChangeNetModelAdapter",
                inputs={"t1_id": asset_ids[0], "t2_id": asset_ids[1]},
                depends_on=[reg_node.id],
                estimated_vram_mb=2500,
                estimated_latency_sec=1.5,
            )
            dag.add_node(change_node)

            # Step D: Spectral indices delta calculation
            spectral_node = MissionNode(
                id="step_4_spectral_deltas",
                node_type=NodeType.SPECTRAL_INDEX,
                name="Multispectral Index Deltas (ΔNDVI, ΔNDBI, ΔNDWI)",
                tool_or_model="SpectralIndexCalculator",
                inputs={"t1_id": asset_ids[0], "t2_id": asset_ids[1]},
                depends_on=[reg_node.id],
                estimated_vram_mb=300,
                estimated_latency_sec=0.3,
            )
            dag.add_node(spectral_node)

            # Step E: Semantic Land-Cover Transition Mapping
            semantic_node = MissionNode(
                id="step_5_semantic_classification",
                node_type=NodeType.SEMANTIC_CHANGE,
                name="Semantic Land Cover Transition Categorization",
                tool_or_model="SemanticChangeClassifier",
                inputs={"change_mask_dep": change_node.id, "spectral_dep": spectral_node.id},
                depends_on=[change_node.id, spectral_node.id],
                estimated_vram_mb=400,
                estimated_latency_sec=0.4,
            )
            dag.add_node(semantic_node)
            last_step = semantic_node.id

            # Step F: If multi-modal SAR available, add fusion node
            if spec.intent == MissionIntent.COMPOUND_INVESTIGATION or len(asset_ids) >= 3:
                fusion_node = MissionNode(
                    id="step_6_cross_modal_fusion",
                    node_type=NodeType.SPATIAL_FUSION,
                    name="Spatial Optical-SAR Cross Modal Corroboration",
                    tool_or_model="SpatialFusionEngine",
                    inputs={"optical_dep": change_node.id, "sar_id": asset_ids[-1]},
                    depends_on=[change_node.id],
                    estimated_vram_mb=800,
                    estimated_latency_sec=0.6,
                )
                dag.add_node(fusion_node)

                disagree_node = MissionNode(
                    id="step_7_disagreement_analysis",
                    node_type=NodeType.DISAGREEMENT_ANALYSIS,
                    name="Sensor Disagreement Physical Diagnosis",
                    tool_or_model="SensorDisagreementEngine",
                    inputs={"fusion_dep": fusion_node.id},
                    depends_on=[fusion_node.id],
                    estimated_vram_mb=200,
                    estimated_latency_sec=0.2,
                )
                dag.add_node(disagree_node)
                last_step = disagree_node.id

        elif spec.intent == MissionIntent.CROSS_MODAL_FUSION:
            compat_node = MissionNode(
                id="step_1_check_compatibility",
                node_type=NodeType.COMPATIBILITY_CHECK,
                name="Optical-SAR Sensor Compatibility Check",
                tool_or_model="CompatibilityEngine",
                inputs={"asset_1": asset_ids[0], "asset_2": asset_ids[1]},
                depends_on=[val_node.id],
                estimated_vram_mb=100,
                estimated_latency_sec=0.1,
            )
            dag.add_node(compat_node)

            sar_node = MissionNode(
                id="step_2_sar_processing",
                node_type=NodeType.SAR_PREPROCESSING,
                name="SAR Calibration & Lee Speckle Filtering",
                tool_or_model="SARProcessor",
                inputs={"sar_id": asset_ids[1]},
                depends_on=[compat_node.id],
                estimated_vram_mb=500,
                estimated_latency_sec=0.7,
            )
            dag.add_node(sar_node)

            fusion_node = MissionNode(
                id="step_3_spatial_fusion",
                node_type=NodeType.SPATIAL_FUSION,
                name="Spatial Cross-Modal Water & Feature Fusion",
                tool_or_model="SpatialFusionEngine",
                inputs={"optical_id": asset_ids[0], "sar_dep": sar_node.id},
                depends_on=[compat_node.id, sar_node.id],
                estimated_vram_mb=800,
                estimated_latency_sec=0.6,
            )
            dag.add_node(fusion_node)

            disagree_node = MissionNode(
                id="step_4_disagreement_diagnosis",
                node_type=NodeType.DISAGREEMENT_ANALYSIS,
                name="Sensor Discrepancy Diagnosis & Quality Gating",
                tool_or_model="SensorDisagreementEngine",
                inputs={"fusion_dep": fusion_node.id},
                depends_on=[fusion_node.id],
                estimated_vram_mb=200,
                estimated_latency_sec=0.2,
            )
            dag.add_node(disagree_node)
            last_step = disagree_node.id

        # 3. Final Evidence Synthesis Node
        synth_node = MissionNode(
            id="step_final_evidence_synthesis",
            node_type=NodeType.EVIDENCE_SYNTHESIS,
            name="Evidence-Gated Answer Synthesis & Confidence Attribution",
            tool_or_model="EvidenceSynthesisEngine",
            inputs={"query": spec.query},
            depends_on=[last_step],
            estimated_vram_mb=100,
            estimated_latency_sec=0.2,
        )
        dag.add_node(synth_node)

        dag.compile()
        return dag
