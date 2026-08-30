# SatQuery AI — System Architecture (v1.0)

This document details the system architecture, component boundaries, domain models, geospatial processing pipelines, and GPU memory budget of SatQuery AI.

---

## 1. High-Level Architecture Overview

SatQuery AI separates perception, reasoning, and explanation into modular layers:

```text
                           ┌──────────────────────────────────────────────┐
                           │            Next.js Web Frontend              │
                           │  (React, TypeScript, Tailwind, Canvas Map)  │
                           └──────────────────────┬───────────────────────┘
                                                  │ HTTP / REST / Multipart
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI Backend Engine                              │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ APPLICATION LAYER (Agent / Orchestrator / Pipeline Execution)             │  │
│  │  - Intent Router (Rule-based / Ollama)                                    │  │
│  │  - Tool Registry & Controller                                             │  │
│  │  - Execution Tracer (Observable Steps)                                    │  │
│  └─────────────────────────────────────┬─────────────────────────────────────┘  │
│                                        │                                        │
│  ┌─────────────────────────────────────▼─────────────────────────────────────┐  │
│  │ DOMAIN LAYER (Perception & Scientific Computation)                        │  │
│  │  - Geospatial Core (rasterio, pyproj, shapely, tiling, CRS, area)         │  │
│  │  - Specialist Models (GeoChat VLM, DOFA, Siamese Change, CDVQA)           │  │
│  │  - Evidence Engine (Provenance Graph, Computed Confidence)                │  │
│  └─────────────────────────────────────┬─────────────────────────────────────┘  │
│                                        │                                        │
│  ┌─────────────────────────────────────▼─────────────────────────────────────┐  │
│  │ INFRASTRUCTURE LAYER (Hardware & Storage)                                 │  │
│  │  - GPUManager (Sequential Load / Unload, VRAM Tracking, 8 GB Ceiling)     │  │
│  │  - Safe Storage Manager (UUIDs, Path Traversal Defense, Dynamic Previews) │  │
│  │  - Database (PostgreSQL/PostGIS & SQLite Provenance Store)                │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Canonical Domain Models

All operations revolve around four primary entities:

### 1. Image Asset (`ImageAsset`)
Represents an ingested raster with verified spatial references:
```json
{
  "id": "img_a8f190c2",
  "path": "/data/uploads/img_a8f190c2_sentinel2.tif",
  "preview_url": "/api/v1/images/img_a8f190c2/preview",
  "modality": "optical",
  "acquisition_date": "2026-01-15T10:30:00Z",
  "crs": "EPSG:32643",
  "width": 4096,
  "height": 4096,
  "band_count": 4,
  "bounds": {
    "min_x": 500000.0, "min_y": 3000000.0,
    "max_x": 540960.0, "max_y": 3040960.0
  }
}
```

### 2. Area of Interest (`AOI`)
Defines the spatial polygon boundary for querying and analysis:
```json
{
  "id": "aoi_b4e912",
  "name": "Bengaluru Urban Zone",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "crs": "EPSG:4326"
}
```

### 3. Analysis Job (`AnalysisJob`)
Records the execution of a perception model or workflow:
```json
{
  "id": "job_991f2c",
  "aoi_id": "aoi_b4e912",
  "task": "bi_temporal_change",
  "status": "completed",
  "inputs": ["img_01", "img_02"],
  "outputs": {
    "change_percent": 13.8,
    "changed_area_m2": 42150.0,
    "regions_geojson": { "type": "FeatureCollection", "features": [...] }
  }
}
```

### 4. Evidence Object (`Evidence`)
Grounds claims with audit traces and computed confidence:
```json
{
  "id": "evi_8819ab",
  "claim": "Built-up land cover increased by 13.8% (42,150 m²)",
  "source_analysis": "job_991f2c",
  "model_used": "siamese_change_detector_v1",
  "confidence": {
    "overall": 0.89,
    "model_score": 0.91,
    "registration_quality": 0.95,
    "sar_agreement": 0.82
  },
  "artifacts": ["mask_preview.png", "changed_polygons.geojson"]
}
```

---

## 3. GPU Memory Budget & Sequential Execution

### 8 GB GDDR6 VRAM Constraint (NVIDIA RTX 4060)

```text
               ┌────────────────────────────────────────────────────────┐
               │              8.0 GB Physical VRAM Ceiling              │
               └────────────────────────────────────────────────────────┘
               │                                                        │
               ├─ System & PyTorch Context Overhead:            ~0.8 GB  │
               ├─ Dynamic Peak Working Memory (Activations):    ~1.2 GB  │
               └─ Maximum Resident Model Capacity:              ~6.0 GB  │
```

- **GeoChat-7B (VLM)**: ~4.0 - 4.5 GB in 4-bit NF4 precision.
- **DOFA (ViT-Base)**: ~0.7 - 1.2 GB in FP16 precision.
- **Change Detector**: ~0.3 - 0.8 GB in FP16/FP32 precision.

The `GPUManager` guarantees that heavy models are loaded sequentially on demand and unloaded with `torch.cuda.empty_cache()` immediately after inference.
