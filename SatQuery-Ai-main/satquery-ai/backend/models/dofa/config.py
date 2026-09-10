"""Configuration and wavelength conditioning for DOFA Multimodal EO Foundation Model."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List


# Sensor wavelength centers in micrometers (um) or millimeters (mm)
SENSOR_WAVELENGTHS = {
    "sentinel2_optical": [0.490, 0.560, 0.665, 0.842],  # Blue, Green, Red, NIR (um)
    "sentinel1_sar_cband": [55.5],                      # C-band wavelength in mm
    "rgb_generic": [0.650, 0.550, 0.450],               # Standard RGB (um)
}


@dataclass
class DOFAConfig:
    model_name: str = "DOFA-ViT-Base"
    checkpoint_dir: Path = Path("./checkpoints/dofa")
    embed_dim: int = 768
    num_heads: int = 12
    depth: int = 12
    fusion_hidden_dim: int = 256
    num_classes: int = 6  # Water, Built-up, Vegetation, Bare Soil, Agriculture, Wetland
