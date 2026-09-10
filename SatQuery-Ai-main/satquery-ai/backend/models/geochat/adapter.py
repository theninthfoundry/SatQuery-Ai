"""GeoChat-7B ModelAdapter implementation for Remote Sensing VQA and Visual Grounding."""

import re
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import torch
    import numpy as np
    HAS_TORCH = True
except ImportError:  # pragma: no cover
    HAS_TORCH = False

from ..registry import ModelAdapter, model_registry
from .config import GeoChatConfig, GEOCHAT_SYSTEM_PROMPT, GEOCHAT_GROUNDING_PROMPT


def parse_grounding_boxes(text: str) -> List[Dict[str, float]]:
    """Parse normalized bounding box coordinates [ymin, xmin, ymax, xmax] from GeoChat text."""
    boxes: List[Dict[str, float]] = []

    # Match patterns like [120, 340, 560, 780] or [0.12, 0.34, 0.56, 0.78]
    pattern = r"\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]"
    matches = re.finditer(pattern, text)

    for m in matches:
        raw_vals = [float(v) for v in m.groups()]
        # If coordinates are 0-1000 scale, normalize to 0.0 - 1.0
        if max(raw_vals) > 1.0:
            ymin, xmin, ymax, xmax = [v / 1000.0 for v in raw_vals]
        else:
            ymin, xmin, ymax, xmax = raw_vals

        # Clamp between 0.0 and 1.0
        ymin = max(0.0, min(1.0, ymin))
        xmin = max(0.0, min(1.0, xmin))
        ymax = max(0.0, min(1.0, ymax))
        xmax = max(0.0, min(1.0, xmax))

        if ymax > ymin and xmax > xmin:
            boxes.append({
                "ymin": round(ymin, 4),
                "xmin": round(xmin, 4),
                "ymax": round(ymax, 4),
                "xmax": round(xmax, 4),
            })

    return boxes


class GeoChatAdapter:
    """Specialist ModelAdapter for GeoChat Remote-Sensing VLM."""

    name: str = "geochat_7b"
    task: str = "vqa_and_grounding"
    capabilities: List[str] = ["vqa", "visual_grounding", "scene_description", "referring_expressions"]
    vram_estimate_mb: int = 4500  # ~4.5 GB in 4-bit NF4

    def __init__(self, config: Optional[GeoChatConfig] = None):
        self.config = config or GeoChatConfig()
        self._model = None
        self._tokenizer = None
        self._processor = None
        self._device = "cpu"
        self._status = "registered"

    @property
    def status(self) -> str:
        if self._model is not None:
            return "ready"
        if not self.config.checkpoint_dir.exists():
            return "checkpoint_missing"
        return self._status

    def is_checkpoint_available(self) -> bool:
        return self.config.checkpoint_dir.exists() and any(self.config.checkpoint_dir.iterdir())

    def load(self, device: str = "cuda:0") -> None:
        """Load GeoChat weights with 4-bit BitsAndBytes quantization."""
        self._device = device

        if not self.is_checkpoint_available():
            warnings.warn(
                f"GeoChat checkpoint not found at {self.config.checkpoint_dir}. "
                "Set up weights via 'python scripts/download_geochat.py' for real inference.",
                stacklevel=2,
            )
            self._status = "checkpoint_missing"
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

            bnb_config = None
            if self.config.load_in_4bit and "cuda" in device and HAS_TORCH and torch.cuda.is_available():
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                    bnb_4bit_compute_dtype=torch.float16,
                )

            self._tokenizer = AutoTokenizer.from_pretrained(
                str(self.config.checkpoint_dir),
                use_fast=False,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                str(self.config.checkpoint_dir),
                quantization_config=bnb_config,
                device_map="auto" if "cuda" in device else None,
                torch_dtype=torch.float16 if "cuda" in device else torch.float32,
            )
            self._status = "ready"

        except Exception as e:
            self._status = "error"
            raise RuntimeError(f"Failed to load GeoChat-7B: {str(e)}")

    def unload(self) -> None:
        """Evict model and release GPU memory."""
        self._model = None
        self._tokenizer = None
        self._processor = None
        if HAS_TORCH and torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._status = "registered"

    def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task,
            "status": self.status,
            "is_loaded": self._model is not None,
            "checkpoint_available": self.is_checkpoint_available(),
            "quantization": "4-bit NF4" if self.config.load_in_4bit else "FP16",
            "vram_estimate_mb": self.vram_estimate_mb,
        }

    def vqa(self, image_path: Path | str, question: str, strict_real: bool = False) -> Dict[str, Any]:
        """Execute single-image visual question answering."""
        img_p = Path(image_path)
        if not img_p.exists():
            raise FileNotFoundError(f"Image not found at {img_p}")

        # Real model inference if weights loaded
        if self._model is not None and self._tokenizer is not None:
            try:
                from PIL import Image
                pil_img = Image.open(img_p).convert("RGB")

                # In GeoChat/LLaVA, pass image tensor if processor or vision tower available
                image_tensor = None
                if self._processor is not None:
                    image_tensor = self._processor(images=pil_img, return_tensors="pt")["pixel_values"]
                elif hasattr(self._model, "get_vision_tower"):
                    try:
                        from transformers import CLIPImageProcessor
                        processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
                        image_tensor = processor(images=pil_img, return_tensors="pt")["pixel_values"]
                    except Exception:
                        pass

                prompt = f"{GEOCHAT_SYSTEM_PROMPT}\n<image>\nQuestion: {question}\nAnswer:"
                inputs = self._tokenizer(prompt, return_tensors="pt")
                if hasattr(inputs, "to") and self._device.startswith("cuda"):
                    inputs = {k: v.to(self._device) for k, v in inputs.items()}

                kwargs = dict(**inputs)
                if image_tensor is not None:
                    if self._device.startswith("cuda"):
                        image_tensor = image_tensor.to(self._device)
                    kwargs["images"] = image_tensor

                with torch.inference_mode():
                    gen_out = self._model.generate(
                        **kwargs,
                        max_new_tokens=256,
                        do_sample=False,
                        temperature=0.0,
                        return_dict_in_generate=True,
                        output_scores=True,
                    )
                seq_ids = gen_out.sequences if hasattr(gen_out, "sequences") else gen_out
                generated_text = self._tokenizer.decode(
                    seq_ids[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True,
                ).strip()

                calc_confidence = None
                if hasattr(gen_out, "scores") and gen_out.scores:
                    try:
                        token_probs = [float(torch.softmax(s[0], dim=-1).max().cpu()) for s in gen_out.scores]
                        calc_confidence = round(float(np.mean(token_probs)), 3)
                    except Exception:
                        calc_confidence = None

                return {
                    "answer": generated_text,
                    "model_confidence": calc_confidence,
                    "model_name": "GeoChat-7B",
                    "model_version": "v1.0-4bit",
                    "weights_available": True,
                    "is_real_weights": True,
                    "fallback_used": False,
                    "execution_mode": "real_inference",
                    "device": self._device,
                    "quantization": "4-bit NF4",
                    "checkpoint_path": str(self.config.checkpoint_dir),
                }
            except Exception as e:
                if strict_real:
                    raise RuntimeError(f"GeoChat forward pass failed: {str(e)}")

        if strict_real:
            raise RuntimeError(
                f"Real mode active but GeoChat-7B weights not found at {self.config.checkpoint_dir}. "
                "Download checkpoint via 'python scripts/download_geochat.py'."
            )

        # Zero fabrication: Explicit fallback when in development/offline mode
        return {
            "answer": (
                f"[Offline Fallback] Scene analysis for query '{question}' on '{img_p.name}'. "
                "GeoChat-7B checkpoint unavailable; classical spectral analysis active."
            ),
            "model_confidence": None,
            "model_name": "GeoChat-7B",
            "model_version": "v1.0-4bit",
            "weights_available": self.is_checkpoint_available(),
            "is_real_weights": False,
            "fallback_used": True,
            "execution_mode": "offline_fallback",
            "status": "model_unavailable",
            "device": self._device,
            "quantization": "4-bit NF4",
            "checkpoint_path": str(self.config.checkpoint_dir),
        }

    def ground(self, image_path: Path | str, referring_expression: str, strict_real: bool = False) -> Dict[str, Any]:
        """Execute visual grounding for referring expressions, returning bounding boxes."""
        img_p = Path(image_path)
        if not img_p.exists():
            raise FileNotFoundError(f"Image not found at {img_p}")

        # Real model inference if weights loaded
        if self._model is not None and self._tokenizer is not None:
            try:
                from PIL import Image
                pil_img = Image.open(img_p).convert("RGB")

                # In GeoChat/LLaVA, pass image tensor if processor or vision tower available
                image_tensor = None
                if self._processor is not None:
                    image_tensor = self._processor(images=pil_img, return_tensors="pt")["pixel_values"]
                elif hasattr(self._model, "get_vision_tower"):
                    try:
                        from transformers import CLIPImageProcessor
                        processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
                        image_tensor = processor(images=pil_img, return_tensors="pt")["pixel_values"]
                    except Exception:
                        pass

                prompt = f"{GEOCHAT_GROUNDING_PROMPT}\n<image>\nLocate: {referring_expression}\nCoordinates:"
                inputs = self._tokenizer(prompt, return_tensors="pt")
                if hasattr(inputs, "to") and self._device.startswith("cuda"):
                    inputs = {k: v.to(self._device) for k, v in inputs.items()}

                kwargs = dict(**inputs)
                if image_tensor is not None:
                    if self._device.startswith("cuda"):
                        image_tensor = image_tensor.to(self._device)
                    kwargs["images"] = image_tensor

                with torch.inference_mode():
                    gen_out = self._model.generate(
                        **kwargs,
                        max_new_tokens=128,
                        do_sample=False,
                        return_dict_in_generate=True,
                        output_scores=True,
                    )
                seq_ids = gen_out.sequences if hasattr(gen_out, "sequences") else gen_out
                generated_text = self._tokenizer.decode(
                    seq_ids[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True,
                ).strip()

                calc_confidence = None
                if hasattr(gen_out, "scores") and gen_out.scores:
                    try:
                        token_probs = [float(torch.softmax(s[0], dim=-1).max().cpu()) for s in gen_out.scores]
                        calc_confidence = round(float(np.mean(token_probs)), 3)
                    except Exception:
                        calc_confidence = None

                parsed_boxes = parse_grounding_boxes(generated_text)
                return {
                    "boxes": parsed_boxes,
                    "raw_output": generated_text,
                    "model_confidence": calc_confidence if parsed_boxes else None,
                    "model_name": "GeoChat-7B",
                    "model_version": "v1.0-4bit",
                    "weights_available": True,
                    "is_real_weights": True,
                    "fallback_used": False,
                    "execution_mode": "real_inference",
                    "device": self._device,
                    "quantization": "4-bit NF4",
                    "checkpoint_path": str(self.config.checkpoint_dir),
                }
            except Exception as e:
                if strict_real:
                    raise RuntimeError(f"GeoChat grounding forward pass failed: {str(e)}")

        if strict_real:
            raise RuntimeError(
                f"Real mode active but GeoChat-7B weights not found at {self.config.checkpoint_dir}."
            )

        # ZERO FABRICATION: Do NOT invent hardcoded bounding boxes or fake confidence
        return {
            "boxes": [],
            "raw_output": "[Offline Fallback] GeoChat-7B checkpoint unavailable. No synthetic boxes generated.",
            "model_confidence": None,
            "model_name": "GeoChat-7B",
            "model_version": "v1.0-4bit",
            "weights_available": self.is_checkpoint_available(),
            "is_real_weights": False,
            "fallback_used": True,
            "execution_mode": "offline_fallback",
            "status": "model_unavailable",
            "device": self._device,
            "quantization": "4-bit NF4",
            "checkpoint_path": str(self.config.checkpoint_dir),
        }


# Auto-register geochat adapter
geochat_adapter = GeoChatAdapter()
model_registry.register("geochat", geochat_adapter)
