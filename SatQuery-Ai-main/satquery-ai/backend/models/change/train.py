"""Training script for the siamese change-detection model."""

from __future__ import annotations
import argparse
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from .dataset import ChangeDetectionDataset
from .model import ChangeDetectionNet


def train(data_dir: str, epochs: int = 30, batch_size: int = 8, lr: float = 1e-3, out_dir: str = "checkpoints") -> None:
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required to train Siamese ChangeNet. Please install via 'pip install torch'")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    dataset = ChangeDetectionDataset(data_dir)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    model = ChangeDetectionNet().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    best_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for img_a, img_b, mask in loader:
            img_a = img_a.to(device)
            img_b = img_b.to(device)
            mask = mask.to(device)

            optimizer.zero_grad()
            logits = model(img_a, img_b)
            loss = criterion(logits, mask)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(loader))
        print(f"Epoch [{epoch:02d}/{epochs:02d}]  Loss: {avg_loss:.4f}")

        if avg_loss < best_loss:
            best_loss = avg_loss
            ckpt_file = out_path / "best.pt"
            torch.save(model.state_dict(), ckpt_file)
            print(f"  --> Saved new best checkpoint to {ckpt_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Siamese Change-Detection Net")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to LEVIR-CD style dataset root")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out-dir", type=str, default="checkpoints")
    args = parser.parse_args()

    train(args.data_dir, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, out_dir=args.out_dir)
