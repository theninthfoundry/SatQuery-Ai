"""
Quick smoke test for the agent router.
Run from the repo root: python tests/test_agent.py
"""
import os
import sys

CASES = [
    ("How many buildings are in this scene?", {"aoi_id": "aoi_1", "image_id": "img_1", "object_class": "building"}),
    ("What changed between these two dates?", {"aoi_id": "aoi_1", "image_before_id": "img_2024", "image_after_id": "img_2026"}),
    ("Does the SAR data support this change?", {"aoi_id": "aoi_1", "change_job_id": "job_1"}),
    ("What is the dominant land cover here?", {"aoi_id": "aoi_1", "image_id": "img_1"}),
    ("What is visible in this image?", {"aoi_id": "aoi_1", "image_id": "img_1"}),
]

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from backend.db import engine
    from backend.models_db import Base
    from backend.agent.router import classify_intent

    Base.metadata.create_all(bind=engine)

    for question, context in CASES:
        intent, conf, params = classify_intent(question)
        print(f"Q: {question}\n -> intent: {intent.value} (conf={conf})\n")

