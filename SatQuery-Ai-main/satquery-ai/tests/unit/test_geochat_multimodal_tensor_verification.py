"""Unit test verifying GeoChat-7B genuine multimodal tensor feeding and offline truthfulness."""

from pathlib import Path
from unittest.mock import MagicMock
import numpy as np
import pytest
import torch

from backend.models.geochat.adapter import GeoChatAdapter, GeoChatConfig


class TestGeoChatMultimodalTensorVerification:

    @pytest.fixture
    def sample_images(self, tmp_path):
        from PIL import Image
        img_river = tmp_path / "river_scene.png"
        img_urban = tmp_path / "urban_scene.png"

        # River image: mostly blue/green
        arr_river = np.zeros((100, 100, 3), dtype=np.uint8)
        arr_river[:, :, 0] = 30
        arr_river[:, :, 1] = 120
        arr_river[:, :, 2] = 220
        Image.fromarray(arr_river).save(img_river)

        # Urban image: mostly gray/brown
        arr_urban = np.zeros((100, 100, 3), dtype=np.uint8)
        arr_urban[:, :, 0] = 180
        arr_urban[:, :, 1] = 170
        arr_urban[:, :, 2] = 160
        Image.fromarray(arr_urban).save(img_urban)

        return img_river, img_urban

    def test_offline_mode_transparent_qualification(self, sample_images):
        """When weights are unavailable, adapter must NOT fabricate boxes or confidences."""
        img_river, _ = sample_images
        adapter = GeoChatAdapter()

        # VQA offline
        vqa_res = adapter.vqa(img_river, "What is visible in this scene?")
        assert vqa_res["is_real_weights"] is False
        assert vqa_res["fallback_used"] is True
        assert vqa_res["model_confidence"] is None, "Offline mode must NOT fabricate confidence"
        assert "[Offline Fallback]" in vqa_res["answer"]

        # Grounding offline
        ground_res = adapter.ground(img_river, "water body")
        assert ground_res["boxes"] == [], "Offline mode must return empty boxes, never hardcoded rectangles"
        assert ground_res["model_confidence"] is None
        assert ground_res["is_real_weights"] is False
        assert ground_res["fallback_used"] is True

    def test_multimodal_tensor_feeding_to_vision_encoder(self, sample_images):
        """Verify that when real model pipeline executes, pixel_values tensors are passed."""
        img_river, img_urban = sample_images

        # Create mock model and processor
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_processor = MagicMock()

        # Mock tokenizer encoding
        mock_tokenizer.return_value = {
            "input_ids": torch.tensor([[1, 2, 3, 4]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]]),
        }
        mock_tokenizer.decode.return_value = "Detected water body [100, 200, 300, 400]"

        # Mock processor creating genuine pixel_values tensor
        def fake_processor(images, return_tensors="pt"):
            img_arr = np.array(images)
            mean_val = float(img_arr.mean())
            tensor = torch.full((1, 3, 336, 336), fill_value=mean_val, dtype=torch.float32)
            return {"pixel_values": tensor}

        mock_processor.side_effect = fake_processor

        # Mock generation output
        gen_mock = MagicMock()
        gen_mock.sequences = torch.tensor([[1, 2, 3, 4, 10, 20]])
        gen_mock.scores = [torch.randn(1, 32000)]
        mock_model.generate.return_value = gen_mock

        adapter = GeoChatAdapter()
        adapter._model = mock_model
        adapter._tokenizer = mock_tokenizer
        adapter._processor = mock_processor

        # 1. Run inference on river image
        adapter.ground(img_river, "water body")
        assert mock_model.generate.called
        call_kwargs = mock_model.generate.call_args[1]
        assert "images" in call_kwargs, "generate() must receive 'images' multimodal tensor"
        river_tensor = call_kwargs["images"]
        assert river_tensor.shape == (1, 3, 336, 336)

        # 2. Run inference on urban image
        adapter.ground(img_urban, "water body")
        urban_tensor = mock_model.generate.call_args[1]["images"]

        # Different visual scenes must produce distinct image conditioning tensors
        assert not torch.equal(river_tensor, urban_tensor), "Distinct imagery must produce distinct pixel_values tensors"
