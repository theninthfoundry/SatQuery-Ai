"""
Smoke test for the land-cover segmentation model.

Generates a synthetic dataset where each image has two known regions
colored to represent two different classes, trains briefly, then checks
that predicted class fractions roughly track the true synthetic
proportions. This is a plumbing + basic-learning-signal check, not an
accuracy benchmark on real imagery.

Run from the repo root: python tests/test_landcover_model.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from models.landcover.train import train
from models.landcover.infer import LandCoverClassifier
from models.landcover.model import CLASSES


def _make_synthetic_dataset(root: str, n: int, size: int) -> None:
    os.makedirs(os.path.join(root, "images"), exist_ok=True)
    os.makedirs(os.path.join(root, "masks"), exist_ok=True)

    rng = np.random.default_rng(4)
    built_up_idx = CLASSES.index("built_up")
    water_idx = CLASSES.index("water")
    other_idx = CLASSES.index("other")

    for i in range(n):
        name = f"tile_{i}.png"

        img = np.full((size, size, 3), 0, dtype=np.uint8)
        mask = np.full((size, size), other_idx, dtype=np.uint8)

        # "built_up": bright gray square, left half
        img[:, : size // 2] = 180
        mask[:, : size // 2] = built_up_idx

        # "water": blue square, right half
        img[:, size // 2 :] = (30, 60, 200)
        mask[:, size // 2 :] = water_idx

        img = img + rng.integers(-10, 10, img.shape).astype(np.int16)
        img = np.clip(img, 0, 255).astype(np.uint8)

        Image.fromarray(img).save(os.path.join(root, "images", name))
        Image.fromarray(mask).save(os.path.join(root, "masks", name))


def main() -> None:
    tmp_dir = tempfile.mkdtemp(prefix="satquery_landcover_smoketest_")
    checkpoint_path = os.path.join(tmp_dir, "checkpoints", "smoketest.pt")
    try:
        data_dir = os.path.join(tmp_dir, "data")
        _make_synthetic_dataset(data_dir, n=16, size=64)
        print(f"synthetic dataset written to {data_dir}")

        train(
            data_dir=data_dir,
            epochs=20,
            batch_size=4,
            lr=1e-3,
            checkpoint_path=checkpoint_path,
            image_size=64,
        )
        assert os.path.exists(checkpoint_path), "checkpoint was not written"
        print("training loop + checkpoint save: OK")

        clf = LandCoverClassifier(checkpoint_path=checkpoint_path, image_size=64)
        assert clf.is_trained, "classifier should report is_trained=True with a real checkpoint"

        result = clf.classify(os.path.join(data_dir, "images", "tile_0.png"))
        for key in ("classes", "confidence", "is_trained"):
            assert key in result, f"missing key in classify() output: {key}"

        print("inference + schema check: OK")
        print("result:", result)

        # True split is ~50% built_up / ~50% water. After 20 epochs on 16
        # tiles this should be roughly right, not exact — this is a
        # learning-signal check, not a pixel-perfect accuracy assertion.
        built_up_frac = result["classes"]["built_up"]
        water_frac = result["classes"]["water"]
        assert built_up_frac + water_frac > 0.7, (
            f"expected built_up+water to dominate the prediction, got {result['classes']}"
        )
        print(f"learning-signal check OK (built_up={built_up_frac}, water={water_frac})")

        print("\nALL CHECKS PASSED (synthetic data only — this is a plumbing test, not an accuracy test)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
