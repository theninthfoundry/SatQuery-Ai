"""
Siamese change-detection network (PRD Section 7.3).

A compact siamese-encoder / difference-decoder architecture — deliberately
small (32/64/128 channels, 3 levels) so it can train on a single consumer
GPU such as an RTX 4060 within a hackathon timeline. This is a correct,
trainable baseline, not a SOTA architecture — swap in something heavier
once you've confirmed the pipeline end-to-end on real data.

Input: two co-registered images of identical shape (B, 3, H, W), H and W
divisible by 4. Output: single-channel change logits at input resolution —
apply sigmoid outside this module to get probabilities.
"""
from __future__ import annotations

import torch
import torch.nn as nn


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


class SiameseEncoder(nn.Module):
    """Shared-weight encoder applied independently to the before and after image."""

    def __init__(self, in_channels: int = 3) -> None:
        super().__init__()
        self.enc1 = ConvBlock(in_channels, 32)
        self.enc2 = ConvBlock(32, 64)
        self.enc3 = ConvBlock(64, 128)
        self.pool = nn.MaxPool2d(2)

    def forward(self, x: torch.Tensor):
        f1 = self.enc1(x)
        f2 = self.enc2(self.pool(f1))
        f3 = self.enc3(self.pool(f2))
        return f1, f2, f3


class ChangeDetectionNet(nn.Module):
    def __init__(self, in_channels: int = 3) -> None:
        super().__init__()
        self.encoder = SiameseEncoder(in_channels)

        self.up3 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec3 = ConvBlock(128, 64)
        self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.dec2 = ConvBlock(64, 32)
        self.out_conv = nn.Conv2d(32, 1, 1)

    def forward(self, img_before: torch.Tensor, img_after: torch.Tensor) -> torch.Tensor:
        b1, b2, b3 = self.encoder(img_before)
        a1, a2, a3 = self.encoder(img_after)

        # Absolute feature difference at each scale is the actual "change"
        # signal — this is the one modeling choice that matters most here.
        d1 = torch.abs(a1 - b1)
        d2 = torch.abs(a2 - b2)
        d3 = torch.abs(a3 - b3)

        x = self.up3(d3)
        x = self.dec3(torch.cat([x, d2], dim=1))
        x = self.up2(x)
        x = self.dec2(torch.cat([x, d1], dim=1))
        logits = self.out_conv(x)
        return logits
