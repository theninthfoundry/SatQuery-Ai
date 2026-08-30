"""
Quick smoke test for the agent router.
Run from the repo root: python tests/test_agent.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.api.db import engine  # noqa: E402
from apps.api.models import Base  # noqa: E402

# detect_change now opens its own DB session to resolve image_id -> path
# (see agent/tools.py), so this "pure routing" test needs the schema to
# exist too — main.py normally does this at app startup; this test has to
# do it explicitly since it never imports main.py.
Base.metadata.create_all(bind=engine)

from apps.api.agent import route_query  # noqa: E402  (import after sys.path setup)

CASES = [
    ("How many buildings are in this scene?", {"aoi_id": "aoi_1", "image_id": "img_1", "object_class": "building"}),
    ("What changed between these two dates?", {"aoi_id": "aoi_1", "image_before_id": "img_2024", "image_after_id": "img_2026"}),
    ("Does the SAR data support this change?", {"aoi_id": "aoi_1", "change_job_id": "job_1"}),
    ("What is the dominant land cover here?", {"aoi_id": "aoi_1", "image_id": "img_1"}),
    ("What is visible in this image?", {"aoi_id": "aoi_1", "image_id": "img_1"}),
]

if __name__ == "__main__":
    for question, context in CASES:
        result = route_query(question, context)
        payload = result.get("result") or result.get("error")
        print(f"Q: {question}\n -> tool: {result['tool_called']}\n -> {payload}\n")
