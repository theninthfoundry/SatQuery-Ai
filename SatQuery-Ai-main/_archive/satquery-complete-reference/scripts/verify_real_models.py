"""
scripts/verify_real_models.py

Run before a demo: reports exactly what is real vs fallback right now,
so nobody discovers a missing checkpoint mid-demonstration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config.settings import PATHS, HARDWARE, FLAGS  # noqa: E402


def check_torch_cuda():
    try:
        import torch
    except ImportError:
        return {"torch_installed": False}
    info = {"torch_installed": True, "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()}
    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["total_vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
    return info


def check_geospatial_stack():
    results = {}
    for mod in ("rasterio", "pyproj", "shapely", "cv2"):
        try:
            __import__(mod)
            results[mod] = True
        except ImportError:
            results[mod] = False
    return results


def check_checkpoints():
    return {
        "geochat": {"path": str(PATHS.geochat), "present": PATHS.geochat.exists()},
        "changenet": {"path": str(PATHS.changenet / "changenet.pt"),
                       "present": (PATHS.changenet / "changenet.pt").exists()},
        "dofa": {"path": str(PATHS.dofa), "present": PATHS.dofa.exists()},
    }


def main():
    print("=" * 70)
    print("SatQuery AI -- Real Model Gate Verification")
    print("=" * 70)

    torch_info = check_torch_cuda()
    print("\n[Torch / CUDA]")
    for k, v in torch_info.items():
        print(f"  {k}: {v}")

    geo_info = check_geospatial_stack()
    print("\n[Geospatial stack]")
    for k, v in geo_info.items():
        mark = "OK" if v else "MISSING"
        print(f"  {k}: {mark}")

    ckpts = check_checkpoints()
    print("\n[Model checkpoints]")
    for name, info in ckpts.items():
        mark = "PRESENT" if info["present"] else "MISSING (fallback will be used)"
        print(f"  {name}: {mark}  -> {info['path']}")

    print("\n[Fallback flags]")
    print(f"  allow_geochat_fallback:   {FLAGS.allow_geochat_fallback}")
    print(f"  allow_changenet_fallback: {FLAGS.allow_changenet_fallback}")
    print(f"  allow_dofa_fallback:      {FLAGS.allow_dofa_fallback}")

    real_ready = (
        torch_info.get("cuda_available", False)
        and all(geo_info.values())
        and ckpts["geochat"]["present"]
    )
    print("\n" + "=" * 70)
    if real_ready:
        print("STATUS: Real GeoChat-7B path is ready.")
    else:
        print("STATUS: Real model path NOT fully ready -- system will run in "
              "fallback mode for missing components (see above). This is a "
              "usable, honest demo state; it is not a failure, but do not "
              "claim GPU-model results are live until this prints READY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
