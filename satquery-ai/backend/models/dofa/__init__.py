"""DOFA multimodal EO foundation model package."""

from .config import DOFAConfig, SENSOR_WAVELENGTHS
from .adapter import DOFAAdapter, dofa_adapter

__all__ = [
    "DOFAConfig",
    "SENSOR_WAVELENGTHS",
    "DOFAAdapter",
    "dofa_adapter",
]
