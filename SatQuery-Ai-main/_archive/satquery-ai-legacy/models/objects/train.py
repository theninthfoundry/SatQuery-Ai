"""
Train the object-counting density model.

    python -m models.objects.train --data-dir /path/to/dataset --epochs 30

Needs real labeled data (point annotations converted to density maps) and
a GPU — smoke-tested here on synthetic data (tests/test_object_count_model.py).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from .dataset import ObjectCountDataset
from .model import ObjectCountNet


def train(
    data_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    checkpoint_path: str,
    image_size: int,
) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ObjectCountDataset(data_dir, image_size=image_size)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    model = ObjectCountNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for imgs, density in loader:
            imgs, density = imgs.to(device), density.to(device)
            optimizer.zero_grad()
            pred = model(imgs)
            loss = criterion(pred, density)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * imgs.size(0)

        print(f"epoch {epoch + 1}/{epochs}  loss={running_loss / len(dataset):.6f}")

    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    print(f"saved checkpoint to {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--checkpoint", default="models/objects/checkpoints/best.pt")
    args = parser.parse_args()
    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.checkpoint, args.image_size)


if __name__ == "__main__":
    main()
