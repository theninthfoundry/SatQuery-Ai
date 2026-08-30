"""
Smoke test for the change-detection model/train/infer pipeline.

Generates a tiny synthetic LEVIR-CD-style dataset on disk, runs one
training epoch, saves a checkpoint, then runs inference through it.
This proves the plumbing is correct (tensor shapes, loss computation,
checkpoint round-trip, mask-to-polygon conversion) — it does NOT validate
model accuracy, which requires real imagery and a real GPU (see README).

Run from the repo root: python tests/test_change_model.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from models.change.train import train
from models.change.infer import ChangeDetector


def _make_synthetic_dataset(root: str, n: int = 6, size: int = 64) -> None:
    for sub in ("A", "B", "label"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)

    rng = np.random.default_rng(0)
    for i in range(n):
        name = f"tile_{i}.png"

        img_a = rng.integers(0, 255, (size, size, 3), dtype=np.uint8)
        Image.fromarray(img_a).save(os.path.join(root, "A", name))

        img_b = img_a.copy()
        img_b[size // 4 : size // 2, size // 4 : size // 2] = 255  # a synthetic "change"
        Image.fromarray(img_b).save(os.path.join(root, "B", name))

        mask = np.zeros((size, size), dtype=np.uint8)
        mask[size // 4 : size // 2, size // 4 : size // 2] = 255
        Image.fromarray(mask).save(os.path.join(root, "label", name))


def main() -> None:
    tmp_dir = tempfile.mkdtemp(prefix="satquery_change_smoketest_")
    checkpoint_path = os.path.join(tmp_dir, "checkpoints", "smoketest.pt")
    try:
        data_dir = os.path.join(tmp_dir, "data")
        _make_synthetic_dataset(data_dir, n=6, size=64)
        print(f"synthetic dataset written to {data_dir}")

        train(
            data_dir=data_dir,
            epochs=2,
            batch_size=2,
            lr=1e-3,
            checkpoint_path=checkpoint_path,
            image_size=64,
        )
        assert os.path.exists(checkpoint_path), "checkpoint was not written"
        print("training loop + checkpoint save: OK")

        detector = ChangeDetector(checkpoint_path=checkpoint_path, image_size=64)
        assert detector.is_trained, "detector should report is_trained=True with a real checkpoint"

        img_before = os.path.join(data_dir, "A", "tile_0.png")
        img_after = os.path.join(data_dir, "B", "tile_0.png")
        result = detector.detect(img_before, img_after)

        for key in ("change_percent", "changed_regions", "model_confidence", "is_trained"):
            assert key in result, f"missing key in detect() output: {key}"
        assert result["changed_regions"]["type"] == "FeatureCollection"
        print("inference + schema check: OK")
        print("result:", result)

        print("\nALL CHECKS PASSED (synthetic data only — this is a plumbing test, not an accuracy test)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
