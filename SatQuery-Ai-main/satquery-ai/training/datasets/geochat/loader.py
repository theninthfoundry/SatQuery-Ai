"""Dataset loader for RSVQA-HR remote sensing visual question answering."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json


class RSVQADataLoader:
    """Loads and formats RSVQA-HR question-answer pairs for vision-language models."""

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)

    def load_split(self, split: str = "val") -> List[Dict[str, Any]]:
        """Load question-answer items for a given split (train/val/test)."""
        split_file = self.data_dir / f"rsvqa_{split}.json"
        if not split_file.exists():
            return []

        with open(split_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        items = []
        for sample in raw_data:
            items.append({
                "id": sample.get("id"),
                "image_path": str(self.data_dir / "images" / sample.get("image_name", "")),
                "question": sample.get("question", ""),
                "answers": sample.get("answers", []),
                "task_type": sample.get("type", "presence"),
            })
        return items
