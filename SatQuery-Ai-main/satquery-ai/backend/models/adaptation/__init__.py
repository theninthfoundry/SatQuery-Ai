"""Remote Sensing Domain Adaptation Package for SatQuery AI.

Implements parameter-efficient fine-tuning (LoRA / QLoRA) on satellite domain
datasets (BigEarthNet-S2, RSVQA) to satisfy SIH26167 adaptation requirements.
"""

from .dataset_bigearthnet import BigEarthNetDataset, BIGEARTHNET_19_CLASSES
from .train_bigearthnet_lora import train_bigearthnet_adaptation, LoRALinear

__all__ = [
    "BigEarthNetDataset",
    "BIGEARTHNET_19_CLASSES",
    "train_bigearthnet_adaptation",
    "LoRALinear",
]
