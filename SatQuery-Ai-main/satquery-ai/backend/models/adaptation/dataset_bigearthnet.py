"""BigEarthNet-S2 Dataset Loader for Remote Sensing Foundation Adaptation.

Loads Sentinel-2 multispectral patches and multi-hot 19-class CORINE
Land Cover (CLC) classification targets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Standard 19 CORINE Land Cover classes for BigEarthNet-S2
BIGEARTHNET_19_CLASSES = [
    "Urban fabric",
    "Industrial or commercial units",
    "Arable land",
    "Permanent crops",
    "Pastures",
    "Complex cultivation patterns",
    "Land principally occupied by agriculture",
    "Broad-leaved forest",
    "Coniferous forest",
    "Mixed forest",
    "Natural grassland and sparsely vegetated areas",
    "Sclerophyllous vegetation",
    "Moors and heathland",
    "Transitional woodland, shrub",
    "Beaches, dunes, sands",
    "Inland wetlands",
    "Coastal wetlands",
    "Inland waters",
    "Marine waters",
]

CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(BIGEARTHNET_19_CLASSES)}


class BigEarthNetDataset(Dataset):
    """PyTorch Dataset for BigEarthNet Sentinel-2 multispectral patches."""

    def __init__(
        self,
        data_dir: Path | str,
        split: str = "train",
        transform: Optional[Any] = None,
        max_samples: Optional[int] = None,
    ):
        self.data_dir = Path(data_dir)
        self.split = split
        self.transform = transform
        self.samples: List[Tuple[Path, np.ndarray]] = []

        self._load_metadata(max_samples)

    def _load_metadata(self, max_samples: Optional[int] = None):
        """Index dataset from BigEarthNet.txt or JSON metadata files."""
        # 1. Look for BigEarthNet.txt or split JSON
        txt_path = self.data_dir / "BigEarthNet.txt"
        json_path = self.data_dir / f"bigearthnet_{self.split}.json"

        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                p_id = r.get("patch_id", "")
                patch_file = self.data_dir / "patches" / f"{p_id}.tif"
                if not patch_file.exists():
                    patch_file = self.data_dir / f"{p_id}.tif"

                labels = r.get("labels", [])
                target = np.zeros(len(BIGEARTHNET_19_CLASSES), dtype=np.float32)
                for lbl in labels:
                    if lbl in CLASS_TO_IDX:
                        target[CLASS_TO_IDX[lbl]] = 1.0

                self.samples.append((patch_file, target))
                if max_samples and len(self.samples) >= max_samples:
                    break

        elif txt_path.exists():
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                parts = line.split(",")
                patch_name = parts[0].strip()
                patch_path = self.data_dir / patch_name
                labels = [p.strip() for p in parts[1:]]

                target = np.zeros(len(BIGEARTHNET_19_CLASSES), dtype=np.float32)
                for lbl in labels:
                    if lbl in CLASS_TO_IDX:
                        target[CLASS_TO_IDX[lbl]] = 1.0

                self.samples.append((patch_path, target))
                if max_samples and len(self.samples) >= max_samples:
                    break

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        if not HAS_TORCH:
            raise RuntimeError("PyTorch is required for BigEarthNet dataset loading")

        patch_path, target_np = self.samples[idx]

        # Load raster or image
        if HAS_RASTERIO and patch_path.suffix.lower() in [".tif", ".tiff"] and patch_path.exists():
            with rasterio.open(patch_path) as ds:
                # Read RGB or RGB+NIR bands (channels first: C, H, W)
                count = min(ds.count, 4)
                arr = ds.read(list(range(1, count + 1))).astype(np.float32)
                # Normalize typical 0-10000 Sentinel-2 reflectance to [0, 1]
                if np.max(arr) > 1.0:
                    arr = np.clip(arr / 10000.0, 0.0, 1.0)
        elif HAS_PIL and patch_path.exists():
            img = Image.open(patch_path).convert("RGB")
            arr = np.array(img, dtype=np.float32).transpose(2, 0, 1) / 255.0
        else:
            # Synthetic tensor for pre-flight pipeline verification
            arr = np.zeros((3, 120, 120), dtype=np.float32)

        tensor_data = torch.from_numpy(arr)
        target_tensor = torch.from_numpy(target_np)

        return tensor_data, target_tensor
