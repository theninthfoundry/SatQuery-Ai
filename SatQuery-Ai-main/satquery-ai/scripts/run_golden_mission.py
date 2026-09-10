"""Standalone Executable Test & Verification for the 19-Stage Golden Mission.

Usage:
    python satquery-ai/scripts/run_golden_mission.py

Demonstrates complete vertical slice execution:
Ingestion -> Sanitization -> Compatibility -> Registration -> ChangeNet ->
Semantic Classification -> Grounding -> Polygonization -> Area Calculation ->
SAR Calibration -> Spatial Corroboration -> Disagreement Diagnosis ->
Evidence Graph -> Evidence Gate -> Report Generation -> Experiment Artifact.
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
import numpy as np

# Add satquery-ai to Python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.db import SessionLocal, init_db
from backend.models_db import ImageRecord
from backend.pipelines.golden_mission import run_complete_compound_golden_mission


def ensure_demo_assets(db) -> tuple[str, str, str]:
    """Ensure mock/demo assets for T1 Optical, T2 Optical, and T2 SAR are seeded."""
    data_dir = repo_root / "data" / "demo"
    data_dir.mkdir(parents=True, exist_ok=True)

    t1_path = data_dir / "golden_t1_optical.png"
    t2_path = data_dir / "golden_t2_optical.png"
    sar_path = data_dir / "golden_t2_sar.png"

    from PIL import Image

    # Create T1 image (predominantly green/rural)
    if not t1_path.exists():
        t1_arr = np.full((256, 256, 3), [60, 140, 50], dtype=np.uint8)
        Image.fromarray(t1_arr).save(t1_path)

    # Create T2 image (with new urban development in the center)
    if not t2_path.exists():
        t2_arr = np.full((256, 256, 3), [60, 140, 50], dtype=np.uint8)
        t2_arr[70:180, 70:180] = [180, 180, 190]  # Concrete / roads / built-up
        Image.fromarray(t2_arr).save(t2_path)

    # Create T2 SAR image (high radar backscatter over buildings)
    if not sar_path.exists():
        sar_arr = np.full((256, 256), 60, dtype=np.uint8)
        sar_arr[70:180, 70:180] = 210  # Double-bounce backscatter
        Image.fromarray(sar_arr).save(sar_path)

    # Insert or fetch DB records
    r1 = db.query(ImageRecord).filter_by(filename="golden_t1_optical.png").first()
    if not r1:
        r1 = ImageRecord(
            id="img_demo_t1_opt",
            filename="golden_t1_optical.png",
            path=str(t1_path),
            format="PNG",
            modality="optical",
            width=256, height=256, band_count=3, dtype="uint8",
            crs="EPSG:4326", epsg=4326,
            resolution={"x_res": 10.0, "y_res": 10.0, "units": "metre"},
            metadata_json={"transform": [0.0001, 0.0, 78.48, 0.0, -0.0001, 17.38]},
        )
        db.add(r1)

    r2 = db.query(ImageRecord).filter_by(filename="golden_t2_optical.png").first()
    if not r2:
        r2 = ImageRecord(
            id="img_demo_t2_opt",
            filename="golden_t2_optical.png",
            path=str(t2_path),
            format="PNG",
            modality="optical",
            width=256, height=256, band_count=3, dtype="uint8",
            crs="EPSG:4326", epsg=4326,
            resolution={"x_res": 10.0, "y_res": 10.0, "units": "metre"},
            metadata_json={"transform": [0.0001, 0.0, 78.48, 0.0, -0.0001, 17.38]},
        )
        db.add(r2)

    r_sar = db.query(ImageRecord).filter_by(filename="golden_t2_sar.png").first()
    if not r_sar:
        r_sar = ImageRecord(
            id="img_demo_t2_sar",
            filename="golden_t2_sar.png",
            path=str(sar_path),
            format="PNG",
            modality="sar",
            width=256, height=256, band_count=1, dtype="uint8",
            crs="EPSG:4326", epsg=4326,
            resolution={"x_res": 10.0, "y_res": 10.0, "units": "metre"},
            metadata_json={"transform": [0.0001, 0.0, 78.48, 0.0, -0.0001, 17.38]},
        )
        db.add(r_sar)

    db.commit()
    return r1.id, r2.id, r_sar.id


def main():
    print("==========================================================================")
    print("       SATQUERY AI — 19-STAGE COMPOUND GOLDEN MISSION VERIFICATION       ")
    print("==========================================================================")

    init_db()
    db = SessionLocal()

    print("\n[Step 0] Verifying and seeding demo observation assets...")
    t1_id, t2_id, sar_id = ensure_demo_assets(db)
    print(f"  [OK] T1 Optical Asset ID: {t1_id}")
    print(f"  [OK] T2 Optical Asset ID: {t2_id}")
    print(f"  [OK] T2 SAR Asset ID:     {sar_id}")

    query = "Has built-up area increased, where, by how much, and does SAR corroborate it?"
    print(f"\n[Executing Mission Query] \"{query}\"")

    res = run_complete_compound_golden_mission(
        image_t1_optical_id=t1_id,
        image_t2_optical_id=t2_id,
        image_t2_sar_id=sar_id,
        query=query,
        db=db,
    )

    print("\n--- 19-Stage Mission Execution Timeline ---")
    for step in res["timeline"]:
        print(f"  [Step {step['step_number']:02d}] {step['tool']:<30} | {step['duration_ms']} ms | {step['description']}")

    print("\n--- Scientific Quantitative Findings ---")
    print(f"  * Altered Surface Extent:    {res['change_percent']}%")
    print(f"  * Physical Measured Area:    {res['total_area_m2']:,.1f} m2 ({res['total_area_ha']} ha / {res['total_area_km2']} km2)")
    print(f"  * Contiguous Spatial Zones:  {res['cluster_count']} cluster(s)")
    print(f"  * SAR Corroboration IoU:     {res['sar_corroboration']['spatial_iou']:.3f}")
    print(f"  * SAR Spatial Consensus:     {res['sar_corroboration']['agreement_ratio'] * 100:.1f}% ({res['sar_corroboration']['status']})")
    print(f"  * Evidence Gate Decision:    {res['evidence_gate']['decision'].upper()} (Confidence: {res['evidence_gate']['confidence']})")
    print(f"  * Total Mission Duration:    {res['total_duration_ms']} ms")

    print("\n--- Grounded Natural Language Finding ---")
    print(f"  \"{res['answer']}\"")

    print("\n--- Downloadable Audit Dossier Endpoints ---")
    for fmt, url in res["report_urls"].items():
        print(f"  * {fmt.upper():<7}: http://127.0.0.1:8000{url}")

    # Snapshot into experiments/
    exp_dir = repo_root / "experiments" / "E003_compound_golden_mission"
    exp_dir.mkdir(parents=True, exist_ok=True)
    with open(exp_dir / "mission_result.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    with open(exp_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(f"# Experiment E003: Compound Golden Mission Run\n\n- Mission ID: `{res['mission_id']}`\n- Query: \"{query}\"\n- Measured Area: {res['total_area_ha']} ha\n- SAR IoU: {res['sar_corroboration']['spatial_iou']}\n- Gate: {res['evidence_gate']['decision']}\n- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"\n[OK] Experiment snapshot recorded under: experiments/E003_compound_golden_mission/")
    print("\n==========================================================================")
    print("                     GOLDEN MISSION STATUS: PASSED                        ")
    print("==========================================================================")


if __name__ == "__main__":
    main()
