"""One-command offline standalone demo launcher for SatQuery AI."""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed_demo_data import seed_demo_scenarios


def main():
    print("==================================================================")
    print("🛰️  SatQuery AI — Autonomous Offline Demo Launcher")
    print("    ISRO Space Technology Multimodal RS Vision-Language Assistant")
    print("==================================================================")

    # 1. Environment & Hardware Verification
    print("\n🔍 Checking Hardware & PyTorch status...")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        print(f"   • PyTorch: Available ({torch.__version__})")
        print(f"   • CUDA GPU: {'Available (' + torch.cuda.get_device_name(0) + ')' if cuda_avail else 'CPU Mode (Safe Fallback)'}")
    except ImportError:
        print("   • PyTorch: Not installed (Running in CPU simulated mode)")

    # 2. Seed Demo Scenarios
    print("\n📦 Seeding Pre-Loaded Remote Sensing Demo Scenarios...")
    seed_demo_scenarios()

    # 3. Launch FastAPI Server
    print("\n🚀 Starting SatQuery AI FastAPI Server on http://127.0.0.1:8000 ...")
    print("   • Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("   • Web Console (Next.js):   http://localhost:3000")
    print("==================================================================\n")

    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
