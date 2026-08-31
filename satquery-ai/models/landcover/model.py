"""
Single-image land-cover segmentation network (the second single-image
task, alongside VQA).

A small U-Net: encoder/decoder with skip connections, producing per-pixel
class logits over a fixed class set. Deliberately similar in shape to
models/change/model.py (same channel sizes) — a segmentation problem, not
a siamese-difference one, so there's exactly one encoder here, not two.

Classes default to: built_up, vegetation, water, other. Change CLASSES if
your actual dataset uses a different label set — the model takes
num_classes as a constructor argument.
"""
from __future__ import annotations

from typing import List

import torch
import torch.nn as nn

CLASSES: List[str] = ["built_up", "vegetation", "water", "other"]


class ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class LandCoverSegNet(nn.Module):
    def __init__(self, in_channels: int = 3, num_classes: int = len(CLASSES)) -> None:
        super().__init__()
        self.num_classes = num_classes

        self.enc1 = ConvBlock(in_channels, 32)
        self.enc2 = ConvBlock(32, 64)
        self.enc3 = ConvBlock(64, 128)
        self.pool = nn.MaxPool2d(2)

        self.up3 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec3 = ConvBlock(128, 64)
        self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec2 = ConvBlock(64, 32)
        self.out_conv = nn.Conv2d(32, num_classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f1 = self.enc1(x)
        f2 = self.enc2(self.pool(f1))
        f3 = self.enc3(self.pool(f2))

        x = self.up3(f3)
        x = self.dec3(torch.cat([x, f2], dim=1))
        x = self.up2(x)
        x = self.dec2(torch.cat([x, f1], dim=1))
        logits = self.out_conv(x)  # (B, num_classes, H, W)
        return logits
