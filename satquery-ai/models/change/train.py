"""
Train the change-detection model on a LEVIR-CD-style directory.

This needs real data and a GPU. Run it on your RTX 4060:

    python -m models.change.train --data-dir /path/to/LEVIR-CD/train --epochs 30

It was smoke-tested on synthetic random tensors during development
(see tests/test_change_model.py) to confirm shapes, the loss, and
checkpoint save/load all work — not to validate accuracy, which requires
real imagery this environment doesn't have.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from .dataset import ChangeDetectionDataset
from .model import ChangeDetectionNet


def dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    intersection = (probs * target).sum(dim=(1, 2, 3))
    union = probs.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    return 1 - ((2 * intersection + eps) / (union + eps)).mean()


def train(
    data_dir: str,
    epochs: int,
    batch_size: int,
    lr: float,
    checkpoint_path: str,
    image_size: int,
) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = ChangeDetectionDataset(data_dir, image_size=image_size)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    model = ChangeDetectionNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    bce = nn.BCEWithLogitsLoss()

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for img_a, img_b, label in loader:
            img_a, img_b, label = img_a.to(device), img_b.to(device), label.to(device)
            optimizer.zero_grad()
            logits = model(img_a, img_b)
            loss = bce(logits, label) + dice_loss(logits, label)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * img_a.size(0)

        print(f"epoch {epoch + 1}/{epochs}  loss={running_loss / len(dataset):.4f}")

    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)
    print(f"saved checkpoint to {checkpoint_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--checkpoint", default="models/change/checkpoints/best.pt")
    args = parser.parse_args()
    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.checkpoint, args.image_size)


if __name__ == "__main__":
    main()
