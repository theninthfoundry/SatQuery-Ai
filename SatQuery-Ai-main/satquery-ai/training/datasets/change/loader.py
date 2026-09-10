"""Dataset loader for LEVIR-CD bi-temporal change detection pairs."""

from pathlib import Path
from typing import Dict, Any, List


class LEVIRCDDataLoader:
    """Loads bi-temporal optical image pairs (T1, T2) and binary ground truth change masks."""

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)

    def load_split(self, split: str = "val") -> List[Dict[str, str]]:
        """Load paired paths (A/T1, B/T2, label/mask) for a given split."""
        split_dir = self.data_dir / split
        dir_a = split_dir / "A"
        dir_b = split_dir / "B"
        dir_label = split_dir / "label"

        if not dir_a.exists() or not dir_b.exists():
            return []

        pairs = []
        for p_a in sorted(dir_a.glob("*.png")):
            p_b = dir_b / p_a.name
            p_mask = dir_label / p_a.name
            if p_b.exists():
                pairs.append({
                    "id": p_a.stem,
                    "t1_path": str(p_a),
                    "t2_path": str(p_b),
                    "mask_path": str(p_mask) if p_mask.exists() else None,
                })
        return pairs
