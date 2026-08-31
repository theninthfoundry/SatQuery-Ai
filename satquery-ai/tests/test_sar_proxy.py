"""
Smoke test for the SAR backscatter change proxy.

Two checks:
  1. A synthetic pair with a real intensity change in half the image should
     report a change fraction close to 50% — this is a plumbing test.
  2. A synthetic pair with NO change (just sensor noise) should report a
     change fraction close to 0% — this is what makes it a real statistic
     rather than something that flags "change" no matter what you feed it.

Run from the repo root: python tests/test_sar_proxy.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from models.sar.proxy import SARChangeProxy


def main() -> None:
    tmp_dir = tempfile.mkdtemp(prefix="satquery_sar_smoketest_")
    try:
        size = 128
        rng = np.random.default_rng(6)

        # Case 1: real change in the right half (much higher backscatter)
        before = rng.integers(40, 60, (size, size)).astype(np.uint8)
        after = before.copy()
        after[:, size // 2 :] = np.clip(
            after[:, size // 2 :].astype(np.int16) + 120, 0, 255
        ).astype(np.uint8)

        before_path = os.path.join(tmp_dir, "sar_before.png")
        after_path = os.path.join(tmp_dir, "sar_after.png")
        Image.fromarray(before).save(before_path)
        Image.fromarray(after).save(after_path)

        proxy = SARChangeProxy(image_size=size)
        result = proxy.compute(before_path, after_path)
        print("case 1 (real change in right half):", result)
        assert 35 <= result["sar_change_percent"] <= 65, (
            f"expected ~50% flagged, got {result['sar_change_percent']}"
        )
        print("case 1: OK — proxy correctly localizes the changed half")

        # Case 2: same image with only sensor-noise-level variation, no
        # real change — should NOT flag a large fraction as changed.
        noisy_before = rng.integers(40, 60, (size, size)).astype(np.uint8)
        noisy_after = np.clip(
            noisy_before.astype(np.int16) + rng.integers(-3, 3, (size, size)), 0, 255
        ).astype(np.uint8)

        noisy_before_path = os.path.join(tmp_dir, "sar_noisy_before.png")
        noisy_after_path = os.path.join(tmp_dir, "sar_noisy_after.png")
        Image.fromarray(noisy_before).save(noisy_before_path)
        Image.fromarray(noisy_after).save(noisy_after_path)

        noisy_result = proxy.compute(noisy_before_path, noisy_after_path)
        print("case 2 (noise only, no real change):", noisy_result)
        assert noisy_result["sar_change_percent"] < 15, (
            f"expected a low false-positive rate on pure noise, got {noisy_result['sar_change_percent']}"
        )
        print("case 2: OK — proxy does not flag noise as change")

        print("\nALL CHECKS PASSED")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
