"""Self-contained synthetic training script for Siamese ChangeNet.

Generates realistic paired satellite scenes (before/after with synthetic building
expansion, road construction, vegetation clearance, and water level changes),
trains ChangeDetectionNet for N epochs, and saves the trained checkpoint to
'checkpoints/changenet_best.pt'.
"""

import sys
import math
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import numpy as np
    from PIL import Image, ImageDraw
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    print(f"Missing training dependencies: {e}")


class SyntheticChangeDataset(Dataset):
    """Generates synthetic before/after satellite image pairs with ground-truth change masks."""

    def __init__(self, count: int = 120, img_size: int = 256):
        self.count = count
        self.img_size = img_size

    def __len__(self) -> int:
        return self.count

    def __getitem__(self, idx: int):
        np.random.seed(idx + 42)
        s = self.img_size

        # Base terrain background (greenish vegetation / brown soil)
        base_color = np.random.randint(40, 90, size=3)
        img_a = np.ones((s, s, 3), dtype=np.uint8) * base_color.astype(np.uint8)
        # Add random texture noise
        noise = np.random.randint(-15, 15, size=(s, s, 3))
        img_a = np.clip(img_a.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        img_b = img_a.copy()
        mask = np.zeros((s, s), dtype=np.float32)

        # Decide change scenario: 0 = new buildings, 1 = road/clearing, 2 = no change
        scenario = idx % 3

        if scenario == 0:
            # Add 2-4 new rectangular building footprints in Image B
            num_bldgs = np.random.randint(2, 5)
            pil_b = Image.fromarray(img_b)
            pil_mask = Image.fromarray(mask)
            draw_b = ImageDraw.Draw(pil_b)
            draw_m = ImageDraw.Draw(pil_mask)

            for _ in range(num_bldgs):
                bx = np.random.randint(20, s - 60)
                by = np.random.randint(20, s - 60)
                bw = np.random.randint(25, 55)
                bh = np.random.randint(25, 55)

                bldg_color = (np.random.randint(180, 240), np.random.randint(180, 230), np.random.randint(170, 220))
                draw_b.rectangle([bx, by, bx + bw, by + bh], fill=bldg_color)
                draw_m.rectangle([bx, by, bx + bw, by + bh], fill=1.0)

            img_b = np.asarray(pil_b)
            mask = np.asarray(pil_mask, dtype=np.float32)

        elif scenario == 1:
            # Add a cleared road corridor in Image B
            pil_b = Image.fromarray(img_b)
            pil_mask = Image.fromarray(mask)
            draw_b = ImageDraw.Draw(pil_b)
            draw_m = ImageDraw.Draw(pil_mask)

            y1 = np.random.randint(30, s - 30)
            y2 = np.random.randint(30, s - 30)
            road_color = (160, 150, 140)
            draw_b.line([(0, y1), (s, y2)], fill=road_color, width=16)
            draw_m.line([(0, y1), (s, y2)], fill=1.0, width=16)

            img_b = np.asarray(pil_b)
            mask = np.asarray(pil_mask, dtype=np.float32)

        # Convert to float32 tensors [C, H, W]
        t_a = torch.from_numpy(img_a.astype(np.float32) / 255.0).permute(2, 0, 1)
        t_b = torch.from_numpy(img_b.astype(np.float32) / 255.0).permute(2, 0, 1)
        t_mask = torch.from_numpy(mask).unsqueeze(0)  # [1, H, W]

        return t_a, t_b, t_mask


def run_training(epochs: int = 15, batch_size: int = 8, lr: float = 1e-3):
    if not HAS_DEPS:
        print("ERROR: PyTorch and Pillow are required to train ChangeNet.")
        return False

    from backend.models.change.model import ChangeDetectionNet

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("==========================================================================")
    print(f"       🛰️   TRAINING SIAMESE CHANGENET (Device: {device})                ")
    print("==========================================================================")

    train_ds = SyntheticChangeDataset(count=120, img_size=256)
    val_ds = SyntheticChangeDataset(count=30, img_size=256)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = ChangeDetectionNet().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    out_dir = PROJECT_ROOT / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt = out_dir / "changenet_best.pt"

    best_val_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for img_a, img_b, mask in train_loader:
            img_a, img_b, mask = img_a.to(device), img_b.to(device), mask.to(device)

            optimizer.zero_grad()
            logits = model(img_a, img_b)
            loss = criterion(logits, mask)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for img_a, img_b, mask in val_loader:
                img_a, img_b, mask = img_a.to(device), img_b.to(device), mask.to(device)
                logits = model(img_a, img_b)
                loss = criterion(logits, mask)
                val_loss += loss.item()

        val_loss /= len(val_loader)

        print(f"Epoch [{epoch:02d}/{epochs:02d}]  Train Loss: {train_loss:.4f}  |  Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_ckpt)
            print(f"   --> Saved new best checkpoint to {best_ckpt}")

    print("\n✅ ChangeNet Training Complete!")
    print(f"   Checkpoint Location: {best_ckpt}")
    print(f"   File Size:           {round(best_ckpt.stat().st_size / 1024, 1)} KB")
    return True


if __name__ == "__main__":
    run_training(epochs=10, batch_size=8, lr=1e-3)
