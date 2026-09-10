"""Dataset loader for BigEarthNet multimodal Sentinel-1 and Sentinel-2 pairs."""

from pathlib import Path
from typing import Dict, Any, List


class BigEarthNetDataLoader:
    """Loads co-registered Sentinel-1 SAR and Sentinel-2 optical multimodal patches."""

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)

    def load_split(self, split: str = "val") -> List[Dict[str, Any]]:
        """Load paired patch paths across optical and radar directories."""
        s2_dir = self.data_dir / "BigEarthNet-S2"
        s1_dir = self.data_dir / "BigEarthNet-S1"

        if not s2_dir.exists() or not s1_dir.exists():
            return []

        patches = []
        for s2_patch in s2_dir.glob("S2A_*"):
            patch_name = s2_patch.name
            s1_patch = s1_dir / patch_name.replace("S2A", "S1A")
            if s1_patch.exists():
                patches.append({
                    "id": patch_name,
                    "s2_path": str(s2_patch),
                    "s1_path": str(s1_patch),
                })
        return patches
