"""Unit tests for GeoChat VLM adapter and bounding box parser."""

import pytest
from pathlib import Path
from backend.models.geochat.adapter import GeoChatAdapter, parse_grounding_boxes
from backend.models.registry import model_registry


def test_parse_grounding_boxes():
    text_1000 = "Detected water body at [200, 300, 600, 800]."
    boxes = parse_grounding_boxes(text_1000)
    assert len(boxes) == 1
    assert boxes[0]["ymin"] == 0.20
    assert boxes[0]["xmin"] == 0.30
    assert boxes[0]["ymax"] == 0.60
    assert boxes[0]["xmax"] == 0.80

    text_norm = "Object located at [0.15, 0.25, 0.45, 0.55]."
    boxes_norm = parse_grounding_boxes(text_norm)
    assert len(boxes_norm) == 1
    assert boxes_norm[0]["ymin"] == 0.15
    assert boxes_norm[0]["xmin"] == 0.25


def test_geochat_adapter_lifecycle():
    adapter = GeoChatAdapter()
    assert adapter.name == "geochat_7b"
    assert "vqa" in adapter.capabilities
    assert "visual_grounding" in adapter.capabilities

    health = adapter.health()
    assert health["name"] == "geochat_7b"
    assert "quantization" in health


def test_geochat_adapter_vqa_and_ground(tmp_path: Path):
    img_file = tmp_path / "scene.png"
    img_file.write_bytes(b"dummy image")

    adapter = GeoChatAdapter()
    vqa_res = adapter.vqa(img_file, "Describe the scene")
    assert "answer" in vqa_res
    assert vqa_res["model_confidence"] > 0.0

    ground_res = adapter.ground(img_file, "Highlight the water body")
    assert "boxes" in ground_res
    assert len(ground_res["boxes"]) > 0
