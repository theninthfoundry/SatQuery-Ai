"""Configuration and prompt templates for GeoChat VLM."""

from pathlib import Path
from dataclasses import dataclass

GEOCHAT_SYSTEM_PROMPT = (
    "You are GeoChat, an expert vision-language model specialized in Earth observation "
    "and remote sensing satellite imagery analysis. Provide concise, grounded, and factual answers."
)

GEOCHAT_GROUNDING_PROMPT = (
    "Please locate and provide bounding box coordinates in the format [ymin, xmin, ymax, xmax] "
    "(normalized between 0 and 1000) for the following referring expression: "
)


@dataclass
class GeoChatConfig:
    model_id: str = "MBZUAI/geochat-7b"
    checkpoint_dir: Path = Path("./checkpoints/geochat")
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    max_new_tokens: int = 512
    temperature: float = 0.2
