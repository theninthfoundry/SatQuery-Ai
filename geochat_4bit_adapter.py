"""
geochat_4bit_adapter.py

4-bit BitsAndBytes loading + inference wrapper for GeoChat-7B, sized for an
8GB RTX 4060. Written to slot into backend/models/geochat/adapter.py.

Design goals for the 8GB budget:
  - NF4 4-bit quantization with double-quant (typically ~4.0-4.5GB for the
    7B LLM backbone alone; leaves headroom for vision tower + KV cache).
  - Sequential model lifecycle: load -> infer -> explicitly unload, rather
    than keeping GeoChat resident alongside ChangeNet/DOFA.
  - No FP16 "shadow" copy: load directly in 4-bit, never .to(fp16) first.
  - Explicit VRAM instrumentation on every call so "it fits" is measured,
    not assumed (Phase 1 Step 6 requirement: don't claim a model fits
    until it has actually been executed).

This is a *reference* adapter shape. GeoChat-7B is LLaVA-architecture
(vision tower + projector + Vicuna-7B LLM), so depending on which
checkpoint/repo you pull, the exact model class may be LlavaForConditionalGeneration
or a custom class shipped with the GeoChat repo. Swap MODEL_CLASS accordingly
-- the quantization/lifecycle logic below is what matters and is class-agnostic.
"""

import gc
import json
import time
import contextlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import torch
from transformers import (
    AutoProcessor,
    AutoModelForCausalLM,  # swap for GeoChat's actual model class if custom
    BitsAndBytesConfig,
)

CHECKPOINT_DIR = Path("./checkpoints/geochat-7b")


# --------------------------------------------------------------------------
# VRAM instrumentation
# --------------------------------------------------------------------------

@dataclass
class VramSnapshot:
    allocated_mb: float
    reserved_mb: float
    max_allocated_mb: float

    @classmethod
    def capture(cls) -> "VramSnapshot":
        if not torch.cuda.is_available():
            return cls(0.0, 0.0, 0.0)
        return cls(
            allocated_mb=torch.cuda.memory_allocated() / 1024**2,
            reserved_mb=torch.cuda.memory_reserved() / 1024**2,
            max_allocated_mb=torch.cuda.max_memory_allocated() / 1024**2,
        )


def reset_peak_stats():
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def hard_free():
    """Explicit unload sequence. Call this after every inference batch
    if another model (ChangeNet, DOFA) needs the VRAM next."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


# --------------------------------------------------------------------------
# Quantization config
# --------------------------------------------------------------------------

def build_4bit_config(compute_dtype: torch.dtype = torch.float16) -> BitsAndBytesConfig:
    """
    NF4 + double quantization. On a 7B decoder this typically lands the
    LLM weights around 4.0-4.5GB (vs ~14GB fp16 / ~7GB fp8). Double-quant
    quantizes the quantization constants themselves for a further ~0.4GB
    saving at negligible quality cost -- worth it when every GB matters.

    compute_dtype=float16 (not bfloat16): RTX 4060 (Ada, not Ampere-server)
    supports bf16 but fp16 has marginally better throughput on consumer
    Ada cards for most inference kernels; switch to bfloat16 if you observe
    numerical instability in generation.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )


# --------------------------------------------------------------------------
# Adapter
# --------------------------------------------------------------------------

class GeoChatAdapter:
    """
    Sequential-load adapter. Instantiate, run inference, then call
    .unload() before the orchestrator hands VRAM to the next specialist
    model (ChangeNet / DOFA). Do NOT keep multiple specialist models
    resident simultaneously on an 8GB card.
    """

    def __init__(self, checkpoint_dir: Path = CHECKPOINT_DIR, max_vram_gb: float = 7.0):
        self.checkpoint_dir = checkpoint_dir
        # Cap what bitsandbytes/accelerate will place on GPU; anything over
        # this spills to CPU RAM via device_map="auto" rather than OOMing.
        # Leave ~1GB headroom below the physical 8GB for CUDA context,
        # fragmentation, and the vision-tower activations during the
        # image forward pass.
        self.max_memory = {0: f"{max_vram_gb}GiB", "cpu": "24GiB"}
        self.model = None
        self.processor = None
        self._load_stats = None

    def load(self):
        if not self.checkpoint_dir.exists():
            raise FileNotFoundError(
                f"No checkpoint at {self.checkpoint_dir}. Run "
                f"scripts/download_weights.py first -- do not fabricate "
                f"a loaded state."
            )

        reset_peak_stats()
        t0 = time.time()

        self.processor = AutoProcessor.from_pretrained(self.checkpoint_dir)

        self.model = AutoModelForCausalLM.from_pretrained(
            self.checkpoint_dir,
            quantization_config=build_4bit_config(),
            device_map="auto",
            max_memory=self.max_memory,
            low_cpu_mem_usage=True,   # streams weights instead of full fp32 staging in RAM
            attn_implementation="sdpa",  # falls back automatically if flash-attn absent
        )
        self.model.eval()

        load_time_s = time.time() - t0
        self._load_stats = {
            "load_time_s": round(load_time_s, 2),
            "vram_after_load": asdict(VramSnapshot.capture()),
            "device_map": str(getattr(self.model, "hf_device_map", "n/a")),
        }
        return self._load_stats

    @torch.inference_mode()
    def infer(self, image, question: str, max_new_tokens: int = 256) -> dict:
        if self.model is None:
            raise RuntimeError("call .load() before .infer()")

        reset_peak_stats()
        inputs = self.processor(images=image, text=question, return_tensors="pt").to(
            self.model.device
        )

        t0 = time.time()
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,       # deterministic decoding for reproducible smoke tests
            temperature=None,
            num_beams=1,
        )
        inference_time_s = time.time() - t0

        answer = self.processor.decode(output_ids[0], skip_special_tokens=True)

        return {
            "answer": answer,
            "inference_time_s": round(inference_time_s, 3),
            "vram_peak_mb": VramSnapshot.capture().max_allocated_mb,
            "device": str(self.model.device),
            "checkpoint": str(self.checkpoint_dir),
        }

    def unload(self):
        del self.model
        del self.processor
        self.model = None
        self.processor = None
        hard_free()
        return asdict(VramSnapshot.capture())


# --------------------------------------------------------------------------
# Phase 1 Step 5 smoke test: proves real inference occurred, not fabricated
# --------------------------------------------------------------------------

def run_smoke_test(image_path: str, question: str, out_path: str =
                    "evaluation/results/phase1_geochat_smoke_test.json"):
    from PIL import Image

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA not available -- fix the environment before claiming "
            "GeoChat inference status. Do not run this on CPU and report "
            "GPU timings."
        )

    adapter = GeoChatAdapter()
    load_stats = adapter.load()

    image = Image.open(image_path).convert("RGB")
    result = adapter.infer(image, question)

    unload_stats = adapter.unload()

    record = {
        "gpu": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "load_stats": load_stats,
        "inference_result": result,
        "vram_after_unload": unload_stats,
        "image_path": image_path,
        "question": question,
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2)

    print(json.dumps(record, indent=2))
    return record


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--out", default="evaluation/results/phase1_geochat_smoke_test.json")
    args = parser.parse_args()

    run_smoke_test(args.image, args.question, args.out)
