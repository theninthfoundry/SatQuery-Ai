"""
Dataset loader for the LEVIR-CD directory layout:

    root/
      A/       # 'before' images
      B/       # 'after' images
      label/   # binary change masks, same filenames as A/B

OSCD ships a different layout — if you use OSCD instead, adapt
`_list_pairs` only; the training loop and model don't care which
dataset produced the tensors.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


class ChangeDetectionDataset(Dataset):
    def __init__(self, root: str, image_size: int = 256) -> None:
        self.root = Path(root)
        self.image_size = image_size
        self.pairs = self._list_pairs()
        if not self.pairs:
            raise FileNotFoundError(
                f"No image pairs found under {self.root} — expected A/, B/, label/ "
                "subfolders with matching filenames (LEVIR-CD layout)."
            )

    def _list_pairs(self) -> List[Tuple[Path, Path, Path]]:
        a_dir, b_dir, label_dir = self.root / "A", self.root / "B", self.root / "label"
        if not (a_dir.is_dir() and b_dir.is_dir() and label_dir.is_dir()):
            return []
        names = sorted(p.name for p in a_dir.iterdir() if p.is_file())
        return [
            (a_dir / n, b_dir / n, label_dir / n)
            for n in names
            if (b_dir / n).exists() and (label_dir / n).exists()
        ]

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        a_path, b_path, label_path = self.pairs[idx]
        return self._load_image(a_path), self._load_image(b_path), self._load_label(label_path)

    def _load_image(self, path: Path) -> torch.Tensor:
        img = Image.open(path).convert("RGB").resize((self.image_size, self.image_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        return torch.from_numpy(arr).permute(2, 0, 1)  # (3, H, W)

    def _load_label(self, path: Path) -> torch.Tensor:
        mask = Image.open(path).convert("L").resize((self.image_size, self.image_size))
        arr = (np.asarray(mask, dtype=np.float32) > 127).astype(np.float32)
        return torch.from_numpy(arr).unsqueeze(0)  # (1, H, W)
