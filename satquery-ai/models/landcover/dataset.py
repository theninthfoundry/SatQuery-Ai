"""
Dataset loader for land-cover segmentation:

    root/
      images/   # RGB tiles
      masks/    # single-channel, pixel value = class index (0..num_classes-1),
                 # same filenames as images/

This is a simpler layout than change detection's A/B/label (no temporal
pairing), which is exactly right — this is a single-image task.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


class LandCoverDataset(Dataset):
    def __init__(self, root: str, image_size: int = 64) -> None:
        self.root = Path(root)
        self.image_size = image_size
        self.pairs = self._list_pairs()
        if not self.pairs:
            raise FileNotFoundError(
                f"No image/mask pairs found under {self.root} — expected images/ and "
                "masks/ subfolders with matching filenames."
            )

    def _list_pairs(self) -> List[Tuple[Path, Path]]:
        img_dir, mask_dir = self.root / "images", self.root / "masks"
        if not (img_dir.is_dir() and mask_dir.is_dir()):
            return []
        names = sorted(p.name for p in img_dir.iterdir() if p.is_file())
        return [(img_dir / n, mask_dir / n) for n in names if (mask_dir / n).exists()]

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        img_path, mask_path = self.pairs[idx]
        img = Image.open(img_path).convert("RGB").resize((self.image_size, self.image_size))
        img_arr = np.asarray(img, dtype=np.float32) / 255.0
        img_t = torch.from_numpy(img_arr).permute(2, 0, 1)

        mask = Image.open(mask_path).convert("L").resize((self.image_size, self.image_size), Image.NEAREST)
        mask_arr = np.asarray(mask, dtype=np.int64)
        mask_t = torch.from_numpy(mask_arr)  # (H, W), values are class indices

        return img_t, mask_t
