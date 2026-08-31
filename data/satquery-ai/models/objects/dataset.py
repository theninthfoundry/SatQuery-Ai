"""
Dataset loader for density-map object counting:

    root/
      images/   # RGB tiles
      density/  # .npy float arrays, same spatial size as image_size,
                 # values sum to the true object count in that tile

.npy (not PNG) for density targets because 8-bit quantization would
distort a map whose SUM matters, not just its visual appearance.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


class ObjectCountDataset(Dataset):
    def __init__(self, root: str, image_size: int = 64) -> None:
        self.root = Path(root)
        self.image_size = image_size
        self.pairs = self._list_pairs()
        if not self.pairs:
            raise FileNotFoundError(
                f"No image/density pairs found under {self.root} — expected images/ "
                "(*.png) and density/ (*.npy) subfolders with matching stems."
            )

    def _list_pairs(self) -> List[Tuple[Path, Path]]:
        img_dir, density_dir = self.root / "images", self.root / "density"
        if not (img_dir.is_dir() and density_dir.is_dir()):
            return []
        names = sorted(p.stem for p in img_dir.iterdir() if p.is_file())
        return [
            (img_dir / f"{n}.png", density_dir / f"{n}.npy")
            for n in names
            if (density_dir / f"{n}.npy").exists()
        ]

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        img_path, density_path = self.pairs[idx]
        img = Image.open(img_path).convert("RGB").resize((self.image_size, self.image_size))
        img_arr = np.asarray(img, dtype=np.float32) / 255.0
        img_t = torch.from_numpy(img_arr).permute(2, 0, 1)

        density = np.load(density_path).astype(np.float32)
        density_t = torch.from_numpy(density).unsqueeze(0)  # (1, H, W)

        return img_t, density_t
