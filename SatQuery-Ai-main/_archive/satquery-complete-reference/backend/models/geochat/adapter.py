"""
backend/models/geochat/adapter.py

4-bit BitsAndBytes GeoChat-7B adapter, sized for an 8GB RTX 4060.
This supersedes the repo-root geochat_4bit_adapter.py -- same lifecycle
contract (load -> infer -> unload, sequential, never resident alongside
ChangeNet/DOFA), extended with:
  - task-specific prompt templates (VQA / captioning / grounding)
  - grounding bbox parsing out of GeoChat's text output
  - a CPU-safe fallback path so callers on non-CUDA machines get a clear
    "no GPU" error instead of a silent hang

Requires: torch, transformers, accelerate, bitsandbytes, pillow.
"""
from __future__ import annotations

import gc
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from backend.config.settings import PATHS, HARDWARE

try:
    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM, BitsAndBytesConfig
except ImportError:
    torch = None


PROMPT_TEMPLATES = {
    "vqa": "[Question] {question}",
    "captioning": "[Caption] Describe the land cover, major objects, and overall "
                  "scene context of this remote-sensing image in detail.",
    "grounding": "[Grounding] Identify the region referred to by: \"{referring_expression}\". "
                 "Respond with a bounding box in [ymin, xmin, ymax, xmax] format "
                 "normalized to 0-1000, followed by a one-sentence justification.",
}

BBOX_PATTERN = re.compile(r"\[\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\]")


@dataclass
class VramSnapshot:
    allocated_mb: float
    reserved_mb: float
    max_allocated_mb: float

    @classmethod
    def capture(cls) -> "VramSnapshot":
        if torch is None or not torch.cuda.is_available():
            return cls(0.0, 0.0, 0.0)
        return cls(
            allocated_mb=torch.cuda.memory_allocated() / 1024**2,
            reserved_mb=torch.cuda.memory_reserved() / 1024**2,
            max_allocated_mb=torch.cuda.max_memory_allocated() / 1024**2,
        )


def _reset_peak():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def _hard_free():
    gc.collect()
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def build_4bit_config(compute_dtype=None) -> "BitsAndBytesConfig":
    compute_dtype = compute_dtype or torch.float16
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )


class GeoChatUnavailable(RuntimeError):
    """Raised when the real GeoChat model cannot be loaded (missing
    checkpoint, no CUDA, import error). Callers use this to decide
    whether to fall back -- it is never swallowed silently."""


class GeoChatAdapter:
    def __init__(self, checkpoint_dir: Path = None, max_vram_gb: float = None):
        self.checkpoint_dir = checkpoint_dir or PATHS.geochat
        self.max_vram_gb = max_vram_gb or HARDWARE.geochat_vram_budget_gb
        self.max_memory = {0: f"{self.max_vram_gb}GiB", "cpu": "24GiB"}
        self.model = None
        self.processor = None
        self._load_stats = None

    def is_available(self) -> bool:
        if torch is None:
            return False
        if not torch.cuda.is_available():
            return False
        return self.checkpoint_dir.exists()

    def load(self):
        if torch is None:
            raise GeoChatUnavailable("torch/transformers not installed in this environment.")
        if not torch.cuda.is_available():
            raise GeoChatUnavailable("CUDA not available -- GeoChat requires a GPU.")
        if not self.checkpoint_dir.exists():
            raise GeoChatUnavailable(
                f"No checkpoint at {self.checkpoint_dir}. Run "
                f"scripts/download_geochat.py first."
            )
        _reset_peak()
        t0 = time.time()
        self.processor = AutoProcessor.from_pretrained(self.checkpoint_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.checkpoint_dir,
            quantization_config=build_4bit_config(),
            device_map="auto",
            max_memory=self.max_memory,
            low_cpu_mem_usage=True,
            attn_implementation="sdpa",
        )
        self.model.eval()
        self._load_stats = {
            "load_time_s": round(time.time() - t0, 2),
            "vram_after_load": asdict(VramSnapshot.capture()),
            "device_map": str(getattr(self.model, "hf_device_map", "n/a")),
        }
        return self._load_stats

    @torch.inference_mode() if torch is not None else (lambda f: f)
    def _generate(self, image, prompt: str, max_new_tokens: int) -> dict:
        inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.model.device)
        t0 = time.time()
        output_ids = self.model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False,
            temperature=None, num_beams=1,
        )
        inference_time_s = time.time() - t0
        text = self.processor.decode(output_ids[0], skip_special_tokens=True)
        return {
            "text": text,
            "inference_time_s": round(inference_time_s, 3),
            "vram_peak_mb": VramSnapshot.capture().max_allocated_mb,
        }

    def answer_vqa(self, image, question: str, max_new_tokens: int = 256) -> dict:
        if self.model is None:
            raise RuntimeError("call .load() before inference")
        prompt = PROMPT_TEMPLATES["vqa"].format(question=question)
        out = self._generate(image, prompt, max_new_tokens)
        return {"answer": out["text"], **{k: v for k, v in out.items() if k != "text"}}

    def caption(self, image, max_new_tokens: int = 256) -> dict:
        if self.model is None:
            raise RuntimeError("call .load() before inference")
        out = self._generate(image, PROMPT_TEMPLATES["captioning"], max_new_tokens)
        return {"caption": out["text"], **{k: v for k, v in out.items() if k != "text"}}

    def ground(self, image, referring_expression: str, max_new_tokens: int = 128) -> dict:
        if self.model is None:
            raise RuntimeError("call .load() before inference")
        prompt = PROMPT_TEMPLATES["grounding"].format(referring_expression=referring_expression)
        out = self._generate(image, prompt, max_new_tokens)
        bbox = self._parse_bbox(out["text"])
        if bbox is None:
            raise ValueError(
                f"GeoChat did not emit a parseable bbox for '{referring_expression}': "
                f"{out['text']!r}"
            )
        return {
            "bbox_norm_ymin_xmin_ymax_xmax": bbox,
            "raw_text": out["text"],
            **{k: v for k, v in out.items() if k != "text"},
        }

    @staticmethod
    def _parse_bbox(text: str) -> Optional[list]:
        m = BBOX_PATTERN.search(text)
        if not m:
            return None
        return [float(g) for g in m.groups()]

    def unload(self):
        del self.model
        del self.processor
        self.model = None
        self.processor = None
        _hard_free()
        return asdict(VramSnapshot.capture())


# ---------------------------------------------------------------------------
# Smoke test entrypoint (proves real inference occurred, not fabricated)
# ---------------------------------------------------------------------------
def run_smoke_test(image_path: str, question: str,
                    out_path: str = "evaluation/results/geochat_smoke_test.json"):
    from PIL import Image
    if torch is None or not torch.cuda.is_available():
        raise GeoChatUnavailable("CUDA not available -- cannot run a real smoke test.")
    adapter = GeoChatAdapter()
    load_stats = adapter.load()
    image = Image.open(image_path).convert("RGB")
    result = adapter.answer_vqa(image, question)
    unload_stats = adapter.unload()
    record = {
        "gpu": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "load_stats": load_stats,
        "inference_result": result,
        "vram_after_unload": unload_stats,
        "image_path": image_path,
        "question": question,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    return record


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--out", default="evaluation/results/geochat_smoke_test.json")
    args = parser.parse_args()
    run_smoke_test(args.image, args.question, args.out)
