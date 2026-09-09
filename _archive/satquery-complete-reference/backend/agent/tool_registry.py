"""
backend/agent/tool_registry.py

Layer 3 of the architecture diagram: the predefined registry the agent
selects from. Each ToolSpec is metadata the router uses to validate an
input configuration *before* touching the GPU -- e.g. change detection
requires exactly 2 images of the same modality; fusion requires exactly
1 optical + 1 SAR image.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Modality(str, Enum):
    OPTICAL = "optical"
    SAR = "sar"
    ANY = "any"


class TaskType(str, Enum):
    VQA = "vqa"
    CAPTIONING = "captioning"
    GROUNDING = "grounding"
    CHANGE_DETECTION = "change_detection"
    CHANGE_VQA = "change_vqa"
    FUSION_OPTICAL_SAR = "fusion_optical_sar"
    GOLDEN_MISSION = "golden_mission"  # multi-step combined workflow


@dataclass
class ToolSpec:
    name: str
    task: TaskType
    required_image_count: int
    required_modalities: list  # list[Modality], order-independent
    requires_bitemporal: bool = False
    description: str = ""


TOOL_REGISTRY: dict = {
    TaskType.VQA: ToolSpec(
        name="geochat_vqa",
        task=TaskType.VQA,
        required_image_count=1,
        required_modalities=[Modality.ANY],
        description="Single-image visual question answering via GeoChat-7B.",
    ),
    TaskType.CAPTIONING: ToolSpec(
        name="geochat_captioning",
        task=TaskType.CAPTIONING,
        required_image_count=1,
        required_modalities=[Modality.ANY],
        description="Detailed scene description / land-cover captioning.",
    ),
    TaskType.GROUNDING: ToolSpec(
        name="geochat_grounding",
        task=TaskType.GROUNDING,
        required_image_count=1,
        required_modalities=[Modality.ANY],
        description="Referring-expression -> bounding box -> UTM ground area.",
    ),
    TaskType.CHANGE_DETECTION: ToolSpec(
        name="siamese_changenet",
        task=TaskType.CHANGE_DETECTION,
        required_image_count=2,
        required_modalities=[Modality.ANY],
        requires_bitemporal=True,
        description="Bi-temporal pixel-level change mask -> polygonized clusters.",
    ),
    TaskType.CHANGE_VQA: ToolSpec(
        name="siamese_changenet+geochat",
        task=TaskType.CHANGE_VQA,
        required_image_count=2,
        required_modalities=[Modality.ANY],
        requires_bitemporal=True,
        description="Change detection + natural-language change explanation.",
    ),
    TaskType.FUSION_OPTICAL_SAR: ToolSpec(
        name="dofa_fusion",
        task=TaskType.FUSION_OPTICAL_SAR,
        required_image_count=2,
        required_modalities=[Modality.OPTICAL, Modality.SAR],
        description="Cross-modal optical+SAR corroboration for water/built-up extraction.",
    ),
    TaskType.GOLDEN_MISSION: ToolSpec(
        name="golden_mission_pipeline",
        task=TaskType.GOLDEN_MISSION,
        required_image_count=2,
        required_modalities=[Modality.ANY],
        description="Full urban-expansion demo: change detection + narrative + report.",
    ),
}


def get_tool(task: TaskType) -> ToolSpec:
    if task not in TOOL_REGISTRY:
        raise KeyError(f"No tool registered for task {task}")
    return TOOL_REGISTRY[task]
