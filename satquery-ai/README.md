# SatQuery AI — Phase 0: Geospatial Ingestion Foundation

An interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Natural Language Queries.

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology theme**

---

## 1. Phase 0 Overview

Phase 0 provides a production-grade geospatial ingestion vertical slice, robust CRS handling, dynamic contrast preview generation, model lifecycle management under an 8 GB VRAM constraint, and an interactive Next.js web console.

### Capabilities Matrix

| Capability | Component | Status | Verification |
|---|---|---|---|
| **GeoTIFF Ingestion & Metadata** | `backend/geospatial/` | **Complete (Real)** | Extracts dimensions, CRS, affine transform, resolution, band stats |
| **CRS Inspection & Validation** | `backend/geospatial/crs.py` | **Complete (Real)** | Identifies EPSG, Projected vs Geographic, handles missing CRS |
| **Dynamic Contrast Previews** | `backend/storage/preview.py` | **Complete (Real)** | Generates 2%-98% percentile stretched PNG previews |
| **Path Safety & Storage** | `backend/storage/manager.py` | **Complete (Real)** | Path traversal protection, UUID generation |
| **GPU Lifecycle & VRAM Tracking** | `backend/models/manager.py` | **Complete (Real)** | Sequential load/unload, real PyTorch CUDA VRAM metrics |
| **Model Registry Foundation** | `backend/models/registry.py` | **Complete (Real)** | `ModelAdapter` protocol with honest status reporting |
| **Bi-temporal Change Model** | `backend/models/change/` | **Complete (Real architecture)** | Siamese network architecture & training pipeline |
| **Next.js Web Console** | `apps/web/` | **Complete (Real)** | Drag-and-drop upload, preview canvas, metadata & CRS dashboard |
| **Single-image VLM VQA** | `backend/models/registry.py` | **Phase 1 Target** | Marked `NOT_IMPLEMENTED` (No fake AI) |

---

## 2. Quick Start

### Backend

```bash
# 1. Activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\Activate.ps1 on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run FastAPI backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000` to access the SatQuery interface.

---

## 3. Running Automated Tests

```bash
# Run complete test suite (unit + integration)
pytest -v
```

---

## 4. API Endpoints

- `GET /health` — Root health check
- `GET /api/v1/health` — Detailed health check with hardware & GPU diagnostics
- `POST /api/v1/images/inspect` — Multipart GeoTIFF upload, inspection, and preview generation
- `GET /api/v1/images/{image_id}/preview` — Serve generated web preview PNG
- `GET /api/v1/images/{image_id}` — Retrieve raster metadata
- `GET /api/v1/models` — List registered models and GPU memory status
- `POST /api/v1/query` — Natural language query routing
