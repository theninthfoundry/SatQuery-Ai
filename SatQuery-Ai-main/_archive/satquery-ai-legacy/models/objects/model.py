"""
Object counting via density-map regression (PRD's "second single-image
task" alternative to segmentation — pick whichever the official PS
actually wants; both are implemented here).

Rather than a full anchor-based detector (bounding-box regression + NMS —
real, but a lot more surface area to get right in a hackathon timeline),
this predicts a per-pixel density map whose values sum to the object
count, following the standard crowd-/object-counting approach. Object
locations are recovered from the density map's local peaks at inference
time (see infer.py) — approximate box positions, not learned box sizes.

Honest limitation: this counts generic salient blobs, not any specific
object_class. A real per-class detector needs class-labeled bounding-box
training data (e.g. xView, SpaceNet) — this is the class-agnostic
fallback tier, not a replacement for one.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


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


class ObjectCountNet(nn.Module):
    def __init__(self, in_channels: int = 3) -> None:
        super().__init__()
        self.enc1 = ConvBlock(in_channels, 16)
        self.enc2 = ConvBlock(16, 32)
        self.enc3 = ConvBlock(32, 64)
        self.pool = nn.MaxPool2d(2)

        self.up3 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec3 = ConvBlock(64, 32)
        self.up2 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.dec2 = ConvBlock(32, 16)
        self.out_conv = nn.Conv2d(16, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f1 = self.enc1(x)
        f2 = self.enc2(self.pool(f1))
        f3 = self.enc3(self.pool(f2))

        x = self.up3(f3)
        x = self.dec3(torch.cat([x, f2], dim=1))
        x = self.up2(x)
        x = self.dec2(torch.cat([x, f1], dim=1))
        density = F.relu(self.out_conv(x))  # density must be non-negative
        return density  # (B, 1, H, W)
