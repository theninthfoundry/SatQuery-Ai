"""Dataset loader for Sentinel-2 surface water validation patches."""

from pathlib import Path
from typing import Dict, Any, List


class Sentinel2WaterDataLoader:
    """Loads Sentinel-2 multispectral scenes and ground truth water body reference masks."""

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)

    def load_samples(self) -> List[Dict[str, str]]:
        """Load paired multispectral GeoTIFF and ground truth water masks."""
        img_dir = self.data_dir / "images"
        mask_dir = self.data_dir / "masks"

        if not img_dir.exists() or not mask_dir.exists():
            return []

        samples = []
        for img_path in sorted(img_dir.glob("*.tif")):
            mask_path = mask_dir / img_path.name
            if mask_path.exists():
                samples.append({
                    "id": img_path.stem,
                    "image_path": str(img_path),
                    "mask_path": str(mask_path),
                })
        return samples
