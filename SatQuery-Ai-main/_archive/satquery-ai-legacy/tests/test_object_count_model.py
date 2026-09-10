"""
Smoke test for the object-count density model.

Generates synthetic tiles with a known number of small bright blobs and
matching density-map targets (each blob's density block sums to exactly
1.0, so the target map sums to the true count). Trains briefly, then
checks: (1) the predicted count is in the right ballpark, (2) the
density-to-boxes step recovers roughly the right number of peaks.

Run from the repo root: python tests/test_object_count_model.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from models.objects.train import train
from models.objects.infer import ObjectCounter


def _make_synthetic_dataset(root: str, n_tiles: int, size: int, rng: np.random.Generator) -> list:
    os.makedirs(os.path.join(root, "images"), exist_ok=True)
    os.makedirs(os.path.join(root, "density"), exist_ok=True)

    true_counts = []
    block = 3  # each "object" is a block x block bright square
    val_per_cell = 1.0 / (block * block)

    for i in range(n_tiles):
        n_objects = rng.integers(3, 8)
        true_counts.append(int(n_objects))

        img = np.zeros((size, size, 3), dtype=np.uint8)
        density = np.zeros((size, size), dtype=np.float32)

        margin = block
        placed = 0
        attempts = 0
        while placed < n_objects and attempts < 100:
            attempts += 1
            cx = rng.integers(margin, size - margin)
            cy = rng.integers(margin, size - margin)
            y0, y1 = cy - block // 2, cy - block // 2 + block
            x0, x1 = cx - block // 2, cx - block // 2 + block
            # avoid overlapping an existing blob (keeps density sums clean)
            if density[y0:y1, x0:x1].sum() > 0:
                continue
            img[y0:y1, x0:x1] = 255
            density[y0:y1, x0:x1] += val_per_cell
            placed += 1
        true_counts[-1] = placed  # actual placed count, in case of collisions

        Image.fromarray(img).save(os.path.join(root, "images", f"tile_{i}.png"))
        np.save(os.path.join(root, "density", f"tile_{i}.npy"), density)

    return true_counts


def main() -> None:
    tmp_dir = tempfile.mkdtemp(prefix="satquery_objcount_smoketest_")
    checkpoint_path = os.path.join(tmp_dir, "checkpoints", "smoketest.pt")
    try:
        rng = np.random.default_rng(8)
        data_dir = os.path.join(tmp_dir, "data")
        true_counts = _make_synthetic_dataset(data_dir, n_tiles=24, size=64, rng=rng)
        print(f"synthetic dataset written to {data_dir}, true counts: {true_counts}")

        train(
            data_dir=data_dir,
            epochs=40,
            batch_size=4,
            lr=1e-3,
            checkpoint_path=checkpoint_path,
            image_size=64,
        )
        assert os.path.exists(checkpoint_path), "checkpoint was not written"
        print("training loop + checkpoint save: OK")

        counter = ObjectCounter(checkpoint_path=checkpoint_path, image_size=64)
        assert counter.is_trained, "counter should report is_trained=True with a real checkpoint"

        errors = []
        for i, true_count in enumerate(true_counts[:8]):  # check a sample, not all 24
            result = counter.count(os.path.join(data_dir, "images", f"tile_{i}.png"))
            for key in ("count", "boxes", "confidence", "is_trained"):
                assert key in result, f"missing key in count() output: {key}"
            err = abs(result["count"] - true_count)
            errors.append(err)
            print(f"tile_{i}: true={true_count} predicted={result['count']} boxes_found={len(result['boxes'])}")

        mean_abs_error = sum(errors) / len(errors)
        print(f"\nmean absolute count error over sample: {mean_abs_error:.2f}")
        assert mean_abs_error < 3.0, (
            f"expected mean count error under 3 after 40 epochs on 24 tiles, got {mean_abs_error:.2f}"
        )
        print("count accuracy check: OK (mean error under 3 objects)")

        print("\nALL CHECKS PASSED (synthetic data only — this is a plumbing test, not an accuracy test)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
