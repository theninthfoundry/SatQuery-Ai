"""Unit tests verifying that GeoChatAdapter strictly purges legacy hardcoded boxes and fake confidence."""

import pytest
from pathlib import Path
from PIL import Image

from backend.models.geochat.adapter import GeoChatAdapter


class TestGeoChatNoFallbackBoxes:

    @pytest.fixture
    def sample_image(self, tmp_path):
        img_path = tmp_path / "test_sample.png"
        img = Image.new("RGB", (256, 256), color=(73, 109, 137))
        img.save(img_path)
        return img_path

    def test_ground_water_query_returns_empty_boxes_offline(self, sample_image):
        """Verify that offline/unloaded GeoChat returns boxes: [] and confidence: None without hallucinating coordinates."""
        adapter = GeoChatAdapter(model_path="non_existent_checkpoints_dir")
        # Ensure it is offline
        assert adapter.is_loaded is False

        # Query with historical keywords that previously triggered hardcoded boxes
        res = adapter.ground(sample_image, "water body")

        assert res["boxes"] == []
        assert res["model_confidence"] is None
        assert res["fallback_used"] is True
        assert res["is_real_weights"] is False
        assert res["status"] == "model_unavailable"

        # Explicitly assert that the legacy hardcoded box is NEVER present
        legacy_water_box = {"ymin": 0.20, "xmin": 0.30, "ymax": 0.65, "xmax": 0.75}
        assert legacy_water_box not in res["boxes"]

    def test_ground_largest_lake_query_returns_empty_boxes(self, sample_image):
        """Verify that 'largest water body' query also returns empty boxes on offline GeoChat."""
        adapter = GeoChatAdapter(model_path="non_existent_checkpoints_dir")
        res = adapter.ground(sample_image, "Where is the largest water body?")

        assert res["boxes"] == []
        assert res["model_confidence"] is None
        assert res["fallback_used"] is True

    def test_ground_building_query_returns_empty_boxes(self, sample_image):
        """Verify that 'building' query does not return legacy hardcoded box [0.35, 0.28, 0.52, 0.52]."""
        adapter = GeoChatAdapter(model_path="non_existent_checkpoints_dir")
        res = adapter.ground(sample_image, "commercial buildings")

        assert res["boxes"] == []
        assert res["model_confidence"] is None
        legacy_building_box = {"ymin": 0.28, "xmin": 0.35, "ymax": 0.52, "xmax": 0.52}
        assert legacy_building_box not in res["boxes"]

    def test_vqa_offline_reports_explicit_fallback(self, sample_image):
        """Verify that offline VQA explicitly reports fallback rather than fabricating high confidence."""
        adapter = GeoChatAdapter(model_path="non_existent_checkpoints_dir")
        res = adapter.vqa(sample_image, "Describe the scene land cover")

        assert res["is_real_weights"] is False
        assert res["fallback_used"] is True
        assert res["model_confidence"] is None
        assert "GeoChat weights are not loaded" in res["answer"]
