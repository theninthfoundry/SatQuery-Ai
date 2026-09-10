"""Unit tests verifying ModelRegistry auditable dataset and model provenance taxonomy."""

import pytest
from backend.models.registry import model_registry, ModelMetadata


class TestModelProvenanceRegistry:

    def test_all_provenance_fields_present_in_registry(self):
        """Verify that every registered model provides the complete provenance taxonomy."""
        models = model_registry.list_models()
        assert len(models) >= 3

        required_keys = [
            "name",
            "task",
            "architecture",
            "pretrained_source",
            "task_finetuned",
            "training_dataset",
            "validation_dataset",
            "checkpoint",
            "checkpoint_sha256",
            "runtime_status",
            "evaluation_metrics",
        ]

        for m in models:
            for key in required_keys:
                assert key in m, f"Model '{m.get('name')}' missing required provenance key '{key}'"

    def test_geochat_provenance_truthfulness(self):
        """Verify that GeoChat is truthfully registered as pretrained zero-shot, not falsely trained from scratch."""
        geochat_meta = model_registry.get_provenance("geochat")
        assert geochat_meta is not None
        assert geochat_meta.pretrained_source == "MBZUAI/geochat-7b"
        # Truth state: SatQuery does not falsely claim to have trained GeoChat from scratch
        assert geochat_meta.task_finetuned is False
        assert "RSVQA" in geochat_meta.training_dataset
        assert "VRSBench" in geochat_meta.validation_dataset

    def test_changenet_provenance_prototype_truth(self):
        """Verify that ChangeNet truthfully reports prototype status when real weights are not present."""
        changenet_meta = model_registry.get_provenance("changenet")
        assert changenet_meta is not None
        # Truth state: SatQuery does NOT claim verified LEVIR-CD weights when file is not on disk
        assert changenet_meta.task_finetuned is False
        assert changenet_meta.training_dataset == "synthetic_prototype"
        assert changenet_meta.checkpoint_sha256 is None
        assert changenet_meta.runtime_status == "CLASSICAL_FALLBACK"

    def test_water_body_analyzer_provenance(self):
        """Verify that WaterBodyAnalyzer is documented as a deterministic GIS specialist."""
        water_engine = model_registry.get_engine("water_body_analyzer")
        assert water_engine is not None
        assert water_engine.entity_type == "DETERMINISTIC_ENGINE"
        assert "MNDWI" in water_engine.algorithm
        assert water_engine.runtime_status == "READY_CPU"

    def test_entity_taxonomy_separation(self):
        """Verify strict taxonomy separation between MODEL and DETERMINISTIC_ENGINE."""
        entities = model_registry.list_entities()
        assert "models" in entities
        assert "deterministic_engines" in entities
        assert len(entities["models"]) >= 3
        assert len(entities["deterministic_engines"]) >= 4

        engine_keys = [e["key"] for e in entities["deterministic_engines"]]
        assert "water_body_analyzer" in engine_keys
        assert "sar_processor" in engine_keys
        assert "geodesic_geometry" in engine_keys

