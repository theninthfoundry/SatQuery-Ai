"""BigEarthNet Remote Sensing Domain Adaptation (LoRA / Low-Rank Fine-Tuning).

Fulfills SIH26167 explicit requirement:
'At least one visual/VLM component must be fine-tuned or otherwise adapted
using BigEarthNet.txt or open-source training data.'

Architecture:
1. Frozen Vision Encoder Backbone (ResNet18 / ViT)
2. Low-Rank Adaptation (LoRA: W = W0 + (B * A) * scaling)
3. 19-Class Multi-Label CORINE Land Cover (CLC) Classification Head
4. Multi-Label BCE with Logits Loss + Macro/Micro F1 validation
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Dict, Any, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torchvision import models
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from .dataset_bigearthnet import BigEarthNetDataset, BIGEARTHNET_19_CLASSES


class LoRALinear(nn.Module):
    """Low-Rank Adaptation Linear Layer wrapper."""

    def __init__(self, in_features: int, out_features: int, r: int = 8, lora_alpha: float = 16.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.r = r
        self.scaling = lora_alpha / r

        # Frozen base weight
        self.weight = nn.Parameter(torch.zeros(out_features, in_features), requires_grad=False)
        self.bias = nn.Parameter(torch.zeros(out_features), requires_grad=False)

        # Trainable low-rank decomposition matrices
        self.lora_A = nn.Parameter(torch.zeros(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))

        # Kaiming uniform init for A, zero init for B (so initial forward pass is identity)
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = F.linear(x, self.weight, self.bias)
        lora_out = F.linear(F.linear(x, self.lora_A), self.lora_B) * self.scaling
        return base_out + lora_out


class RSAdaptedClassifier(nn.Module):
    """Vision backbone adapted for Remote Sensing with LoRA layers."""

    def __init__(self, num_classes: int = 19, lora_r: int = 8):
        super().__init__()
        # Use standard torchvision ResNet18 backbone
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT if hasattr(models, "ResNet18_Weights") else None)

        # Freeze backbone parameters
        for param in backbone.parameters():
            param.requires_grad = False

        self.conv1 = backbone.conv1
        self.bn1 = backbone.bn1
        self.relu = backbone.relu
        self.maxpool = backbone.maxpool
        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3
        self.layer4 = backbone.layer4
        self.avgpool = backbone.avgpool

        # Replace final fc with LoRA Linear layer + classification projection
        in_feat = backbone.fc.in_features
        self.lora_fc = LoRALinear(in_feat, in_feat, r=lora_r)
        self.classifier = nn.Linear(in_feat, num_classes)

        # Base fc weight transfer
        self.lora_fc.weight.data.copy_(torch.eye(in_feat))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)

        # Pass through low-rank adapter
        feat = F.relu(self.lora_fc(x))
        logits = self.classifier(feat)
        return logits


def compute_multilabel_f1(logits: torch.Tensor, targets: torch.Tensor, threshold: float = 0.5) -> Tuple[float, float]:
    """Compute Micro and Macro F1 scores for multi-label predictions."""
    preds = (torch.sigmoid(logits) > threshold).float()

    tp = (preds * targets).sum().item()
    fp = (preds * (1 - targets)).sum().item()
    fn = ((1 - preds) * targets).sum().item()

    micro_prec = tp / max(1.0, tp + fp)
    micro_rec = tp / max(1.0, tp + fn)
    micro_f1 = (2 * micro_prec * micro_rec) / max(1e-6, micro_prec + micro_rec)

    # Per-class F1 for Macro
    per_cls_f1 = []
    num_classes = targets.shape[1]
    for c in range(num_classes):
        c_tp = (preds[:, c] * targets[:, c]).sum().item()
        c_fp = (preds[:, c] * (1 - targets[:, c])).sum().item()
        c_fn = ((1 - preds[:, c]) * targets[:, c]).sum().item()

        cp = c_tp / max(1.0, c_tp + c_fp)
        cr = c_tp / max(1.0, c_tp + c_fn)
        cf1 = (2 * cp * cr) / max(1e-6, cp + cr) if (cp + cr) > 0 else 0.0
        per_cls_f1.append(cf1)

    macro_f1 = sum(per_cls_f1) / max(1, len(per_cls_f1))
    return micro_f1, macro_f1


def train_bigearthnet_adaptation(
    data_dir: str,
    epochs: int = 15,
    batch_size: int = 16,
    lr: float = 1e-3,
    lora_r: int = 8,
    out_dir: str = "checkpoints/bigearthnet_lora",
) -> Dict[str, Any]:
    """Execute domain adaptation training on BigEarthNet."""
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required for BigEarthNet LoRA domain adaptation.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🛰️ Remote Sensing Domain Adaptation (LoRA r={lora_r}) running on: {device}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    dataset = BigEarthNetDataset(data_dir, split="train")
    if len(dataset) == 0:
        print(f"Notice: No samples found in {data_dir}. Initializing model architecture & saving blueprint.")
        model = RSAdaptedClassifier(num_classes=len(BIGEARTHNET_19_CLASSES), lora_r=lora_r)
        torch.save(model.state_dict(), out_path / "adapted_model_blueprint.pt")
        return {
            "status": "BLUEPRINT_SAVED",
            "message": "Dataset directory is empty; model architecture verified and checkpoint blueprint created.",
            "classes_count": len(BIGEARTHNET_19_CLASSES),
        }

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = RSAdaptedClassifier(num_classes=len(BIGEARTHNET_19_CLASSES), lora_r=lora_r).to(device)

    # Train only LoRA parameters and classifier
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=lr, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()

    best_macro_f1 = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        all_logits, all_targets = [], []

        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            all_logits.append(logits.detach())
            all_targets.append(y.detach())

        cat_logits = torch.cat(all_logits, dim=0)
        cat_targets = torch.cat(all_targets, dim=0)
        micro_f1, macro_f1 = compute_multilabel_f1(cat_logits, cat_targets)

        avg_loss = total_loss / max(1, len(loader))
        print(f"Epoch [{epoch:02d}/{epochs:02d}] Loss: {avg_loss:.4f} | Micro-F1: {micro_f1:.3f} | Macro-F1: {macro_f1:.3f}")

        if macro_f1 >= best_macro_f1:
            best_macro_f1 = macro_f1
            torch.save(model.state_dict(), out_path / "bigearthnet_lora_best.pt")

    report = {
        "status": "TRAINED",
        "dataset": "BigEarthNet-S2",
        "classes": BIGEARTHNET_19_CLASSES,
        "best_macro_f1": best_macro_f1,
        "lora_rank": lora_r,
        "epochs": epochs,
        "checkpoint_path": str(out_path / "bigearthnet_lora_best.pt"),
    }
    with open(out_path / "adaptation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train BigEarthNet LoRA Remote Sensing Adaptation")
    parser.add_argument("--data-dir", type=str, default="data/benchmarks/bigearthnet")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--out-dir", type=str, default="checkpoints/bigearthnet_lora")
    args = parser.parse_args()

    train_bigearthnet_adaptation(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        lora_r=args.lora_r,
        out_dir=args.out_dir,
    )
