"""Dataset loader for bi-temporal change detection."""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    Dataset = object

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ChangeDetectionDataset(Dataset):
    """Expects root_dir with A/, B/, and label/ subdirectories."""

    def __init__(self, root_dir: str | Path, image_size: int = 256) -> None:
        self.root = Path(root_dir)
        self.image_size = image_size

        self.a_dir = self.root / "A"
        self.b_dir = self.root / "B"
        self.label_dir = self.root / "label"

        if not (self.a_dir.exists() and self.b_dir.exists() and self.label_dir.exists()):
            raise ValueError(
                f"Dataset at {self.root} must contain A/, B/, and label/ subfolders."
            )

        self.filenames: List[str] = sorted(
            p.name for p in self.a_dir.glob("*") if p.suffix.lower() in {".png", ".jpg", ".tif", ".tiff"}
        )

    def __len__(self) -> int:
        return len(self.filenames)

    def _load_image(self, path: Path):
        if not HAS_PIL or not HAS_TORCH:
            return None
        img = Image.open(path).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        return torch.from_numpy(arr).permute(2, 0, 1)

    def _load_mask(self, path: Path):
        if not HAS_PIL or not HAS_TORCH:
            return None
        img = Image.open(path).convert("L").resize((self.image_size, self.image_size), Image.NEAREST)
        arr = (np.asarray(img, dtype=np.float32) > 127).astype(np.float32)
        return torch.from_numpy(arr).unsqueeze(0)

    def __getitem__(self, idx: int):
        fn = self.filenames[idx]
        img_a = self._load_image(self.a_dir / fn)
        img_b = self._load_image(self.b_dir / fn)
        mask = self._load_mask(self.label_dir / fn)
        return img_a, img_b, mask
