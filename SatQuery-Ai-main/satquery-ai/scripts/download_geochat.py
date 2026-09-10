"""Download GeoChat-7B checkpoint from Hugging Face for local 4-bit execution."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings

MODEL_ID = "MBZUAI/geochat-7b"
TARGET_DIR = Path("./checkpoints/geochat")


def download_geochat_weights():
    print(f"🛰️  Target Checkpoint: {MODEL_ID}")
    print(f"📁 Destination Directory: {TARGET_DIR.resolve()}")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download
        print("\n⬇️  Starting snapshot download from Hugging Face Hub...")
        snapshot_download(
            repo_id=MODEL_ID,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False,
            ignore_patterns=["*.msgpack", "*.h5", "*.tflite"],
        )
        print("\n✅ GeoChat-7B Checkpoint successfully downloaded to ./checkpoints/geochat")
    except ImportError:
        print("❌ huggingface_hub is required. Install via: pip install huggingface_hub")
    except Exception as e:
        print(f"❌ Download failed: {str(e)}")


if __name__ == "__main__":
    download_geochat_weights()
