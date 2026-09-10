# SatQuery AI — Final Forensic Audit & Hardening Plan

**SIH26167 · Indian Space Research Organisation (ISRO)**  
**System:** SatQuery AI — Interactive Multimodal Remote Sensing Vision-Language Assistant  
**Auditor Roles:** Principal Engineer, ML Engineer, Geospatial Engineer, Security Lead, QA Lead, Release Engineer  

---

## 1. Executive Summary & Objective
This audit plan establishes the methodology to rigorously verify the operational truth of every claimed capability in SatQuery AI:
- **Zero False Completeness**: Differentiate genuine neural inference from deterministic heuristics, sensor-aware proxies, and offline fallbacks.
- **End-to-End Tracing**: Inspect inputs, validations, pipelines, neural heads, geospatial transformations, evidence synthesis, and multi-format exports.
- **Hardware Envelope**: Validate execution on a single NVIDIA RTX 4060 Laptop (8 GB VRAM budget) under strict sequential model loading and memory eviction.

---

## 2. Discovered Architecture & Runtime Topology

### Frontend (`satquery-ai/apps/web`)
- **Framework**: Next.js 14 (App Router) + Tailwind CSS + TypeScript.
- **Entry Points**:
  - `src/app/page.tsx` — Workspace router.
  - `src/components/MissionWorkspace.tsx` — Scientific intelligence master interface.
  - `src/components/map/GeoWorkspace.tsx` — 60–65% central satellite viewport.
- **API Client**: `src/lib/api.ts` consuming REST API at `http://127.0.0.1:8000`.

### Backend (`satquery-ai/backend`)
- **Framework**: FastAPI (Python 3.10+) + SQLAlchemy + Uvicorn.
- **Entry Point**: `backend/main.py` mounting modular API routers.
- **Database & Storage**: SQLite (`backend/db.py`) + file storage (`data/uploads/`, `data/previews/`).

### Discovered API Routes
1. `GET /api/v1/health` — Hardware, PyTorch, CUDA, and GPU VRAM diagnostics.
2. `POST /api/v1/images/inspect` — GeoTIFF ingestion, CRS validation, metadata parsing, and preview rendering.
3. `GET /api/v1/images` & `GET /api/v1/images/{id}/preview` — Ingested scene catalog and PNG preview streaming.
4. `POST /api/v1/query` — Autonomous 3-layer Agent query dispatch and pipeline routing.
5. `POST /api/v1/analysis/vqa` — Single-image remote sensing visual question answering.
6. `POST /api/v1/analysis/grounding` — Text-guided referring expression visual grounding.
7. `POST /api/v1/analysis/change` — Bi-temporal Siamese ChangeNet change detection & polygonized ground area.
8. `POST /api/v1/analysis/optical-sar` — DOFA optical + SAR radar cross-modal corroboration.
9. `GET /api/v1/reports/{job_id}/{format}` — Downloadable mission dossiers (PDF, GeoJSON, CSV).
10. `GET /api/v1/evaluation/benchmark/{suite}` — Deterministic benchmark evaluation harness.

---

## 3. Forensic Audit Scope (36 Required Capabilities)
1. Single optical/multispectral image ingestion (GTiff/TIFF)
2. Single SAR image ingestion
3. CRS validation & detection (Projected vs Geographic)
4. GSD extraction & pixel dimensions
5. Multi-band statistics calculation
6. Web preview PNG generation
7. Single-image RS-VQA
8. Visual grounding & coordinate normalization
9. Bi-temporal image pair validation & alignment IoU
10. Siamese ChangeNet probability map generation
11. Morphological contour polygonization
12. Reprojected UTM ground area computation ($m^2$ & ha)
13. Optical + SAR pair compatibility check
14. Optical spectral & SAR backscatter ($\sigma^0$ dB) corroboration
15. 3-layer agentic query routing & invalid-workflow rejection
16. Structured Evidence & Provenance graph construction
17. Calibrated ECE Platt-scaling & resolution weighting
18. Multi-format export (PDF, GeoJSON, CSV)
19. Sequential GPU model eviction & memory cleanup
20. Security hardening (Path traversal, file size limits, MIME checks)
