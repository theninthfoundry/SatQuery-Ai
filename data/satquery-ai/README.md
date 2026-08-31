# SatQuery AI — Phase 0 + first real model

The "Phase 0" foundation from the Master PRD (Section 19), plus the first
real (non-stub) capability: `detect_change`, backed by an actual trainable
siamese change-detection network under `models/change/`.

## What's real vs. stubbed, honestly

| Piece | Status |
|---|---|
| Tool registry (`agent/tool_registry.py`) | Real, final shape |
| Agent routing (`agent/router.py`) | Real rule-based router; LLM-assisted mode not yet implemented |
| `detect_change` (`agent/tools.py` + `models/change/`) | **Real architecture, real training script, real inference** — but **untrained**. No checkpoint exists at `models/change/checkpoints/best.pt` because this repo has no GPU and no real LEVIR-CD/OSCD/ISRO-SAC data. Train it on your RTX 4060 (see below) before the number in its answer means anything — the API already says so ("model is untrained") rather than hiding it. |
| `segment_landcover` (`agent/tools.py` + `models/landcover/`) | **Real architecture (single-image U-Net), real training script, real inference** — same "untrained until you train it" honesty as `detect_change`. Default class set: `built_up`, `vegetation`, `water`, `other` — edit `models/landcover/model.py`'s `CLASSES` if your actual label set differs. |
| `sar_corroborate` (`agent/tools.py` + `models/sar/`) | **Real, deterministic signal processing — no learned model, so no "untrained" caveat needed.** A log-ratio backscatter-change statistic (tested to correctly flag ~50% change on a real synthetic shift and ~0% on pure noise), cross-checked against `detect_change`'s optical result. Resolves its own SAR image pair by querying `Image` rows with `sensor='sar'` for the AOI. Schema note: dropped the original `change_job_id` input — there's no persisted analysis-job table yet to resolve one against, so this pulls both SAR and optical pairs straight from the AOI instead. |
| `detect_objects` (`agent/tools.py` + `models/objects/`) | **Real architecture (density-map regression, not a full detector), real training script, real inference.** Tested: 8/8 synthetic tiles found the exact right number of boxes; integrated count within 1 of ground truth. Class-agnostic — counts salient blobs, doesn't discriminate by `object_class`. Schema note: dropped `object_class` from the input for the same reason `sar_corroborate` dropped `change_job_id` — nothing in this implementation could use it. |
| `answer_visual_question` | **Stubbed** — the one remaining stub. Real VQA needs GeoChat-class weights (7B+ params); not worth faking locally, that validation belongs on the RTX 4060/Antigravity track. |
| Image resolution (`routes/query.py`) | Real — queries the DB for the most recently registered `image_id`/`image_before_id`/`image_after_id`, filtered by sensor. |
| Image storage | **Metadata only.** `POST /images` stores a `path` string, nothing uploads or stores actual file bytes. `detect_change` will honestly report "not found on disk" if that path doesn't point to a real file — it will not fabricate a result. |
| API contracts (`routes/`) | Real, matches PRD Section 11 |
| DB schema (`models.py`) | Real, matches PRD Section 12; defaults to local SQLite |
| Geospatial pipeline (PRD Section 9) | Not yet started — `changed_regions` polygons are in **pixel space**, not real-world coordinates, until the affine transform from a real GeoTIFF is wired in |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # now includes torch, opencv, pillow, numpy

# smoke-test the agent router alone (creates a local SQLite schema, no server)
python tests/test_agent.py

# smoke-test the change-detection model on synthetic data (proves the
# pipeline runs correctly — NOT an accuracy test, see the file's docstring)
python tests/test_change_model.py

# run the API (SQLite by default — no docker-compose needed)
uvicorn apps.api.main:app --reload
```

Then try:

```bash
curl -X POST localhost:8000/aoi \
  -H "Content-Type: application/json" \
  -d '{"name": "test-aoi", "geometry": {"type": "Polygon", "coordinates": []}}'

# register two real image files (paths must exist on disk for detect_change to work)
curl -X POST localhost:8000/images \
  -H "Content-Type: application/json" \
  -d '{"aoi_id": "<aoi_id>", "sensor": "optical", "acquisition_date": "2024-01-01T00:00:00", "path": "/abs/path/to/before.png"}'
curl -X POST localhost:8000/images \
  -H "Content-Type: application/json" \
  -d '{"aoi_id": "<aoi_id>", "sensor": "optical", "acquisition_date": "2026-01-01T00:00:00", "path": "/abs/path/to/after.png"}'

curl -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"aoi_id": "<aoi_id>", "question": "What changed between these dates?"}'
```

## Training the models for real

```bash
# change detection — expects root/A, root/B, root/label (LEVIR-CD layout)
python -m models.change.train --data-dir /path/to/LEVIR-CD/train --epochs 30

# land cover — expects root/images, root/masks
python -m models.landcover.train --data-dir /path/to/dataset --epochs 30

# object counting — expects root/images (*.png), root/density (*.npy)
python -m models.objects.train --data-dir /path/to/dataset --epochs 30
```

Do this on the RTX 4060, not in a sandbox. Once a checkpoint exists at
`models/change/checkpoints/best.pt` or `models/landcover/checkpoints/best.pt`,
the corresponding tool in `agent/tools.py` picks it up automatically — no
code changes needed, and the "untrained" caveat disappears from the API's
answers on its own.

## Switching to Postgres/PostGIS

```bash
docker compose up -d
cp .env.example .env   # then export DATABASE_URL or use python-dotenv
```

## Next steps (see PRD Sections 7, 9, and 19)

1. Get real LEVIR-CD (or OSCD, or the actual ISRO/SAC pairs once available)
   onto the RTX 4060 and run `models/change/train.py` for real. Same for
   `models/landcover` and `models/objects` — all three ship untrained.
2. Add the geospatial pipeline (GDAL/Rasterio/GeoPandas): real image
   storage/upload, and swap `_mask_to_pixel_polygons` in `models/change/infer.py`
   for a rasterio-based version so `changed_regions` are real-world
   coordinates, not pixel coordinates.
3. `answer_visual_question` is the last stub. It's the one place a real
   model here would need real VQA weights (GeoChat-class, 7B+ params) —
   not worth faking locally; that validation belongs on the
   Antigravity/RTX 4060 track.
4. Add a persisted `AnalysisJob`/change-result table so `sar_corroborate`
   can do real spatial polygon overlap instead of comparing two independent
   change-percent numbers, and so `detect_objects` could eventually accept
   a real `object_class` filter once class-labeled training data exists.
5. Only after that, build the frontend against these now-real outputs.
