"""Dataset loader for VRSBench referring expression visual grounding."""

from pathlib import Path
from typing import Dict, Any, List
import json


class VRSBenchDataLoader:
    """Loads VRSBench remote sensing referring expressions with bounding box targets."""

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)

    def load_split(self, split: str = "val") -> List[Dict[str, Any]]:
        """Load grounding samples for a given split (train/val/test)."""
        ann_file = self.data_dir / f"vrsbench_{split}.json"
        if not ann_file.exists():
            return []

        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        samples = []
        for item in data:
            samples.append({
                "id": item.get("id"),
                "image_path": str(self.data_dir / "images" / item.get("image_name", "")),
                "expression": item.get("expression", ""),
                "boxes": item.get("boxes", []),  # [[ymin, xmin, ymax, xmax], ...]
                "category": item.get("category", "object"),
            })
        return samples
