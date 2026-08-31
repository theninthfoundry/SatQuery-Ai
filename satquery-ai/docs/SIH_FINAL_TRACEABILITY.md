# SatQuery AI — SIH Final Requirement & Capability Traceability Matrix

**Problem Statement:** SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme  
**Official Title:** *SatQuery AI — Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis*  
**Auditor:** Independent SIH Evaluator & Principal Verification Engineer  

---

## 1. Explicit Status Definitions

To avoid all ambiguity during evaluation, capabilities are tracked under distinct, non-overlapping statuses:

- **IMPLEMENTED**: Codebase architecture, data models, and execution logic are fully written.
- **PIPELINE VERIFIED**: Complete software execution path (input validation, transformation, API, UI) is operational.
- **DEMO VERIFIED**: Pre-seeded with authentic Earth Observation data (Bangalore, Brahmaputra, Sundarbans, Thar Canal).
- **REAL MODEL VERIFIED**: The actual neural network weights (e.g. Siamese ChangeNet PyTorch CNN) are loaded and executing.
- **BENCHMARK VERIFIED**: Full external benchmark dataset tested (or **HARNESS VERIFIED** when running on test sample splits).

---

## 2. Capability Traceability Matrix

| # | SIH Requirement | Pipeline Path | Runtime Test | Real Model Required | Current Execution Status | Concrete Evidence |
|---|---|---|---|:---:|---|---|
| **1** | **Single-Image RS-VQA** | `backend/models/geochat/`, `backend/pipelines/single_image.py` | `POST /api/v1/analysis/vqa` | Yes (GeoChat-7B 4-bit) | **PIPELINE VERIFIED**<br>*(Real Model: Weights On-Demand)* | `geochat/adapter.py`, `scripts/download_geochat.py`, honest offline flag |
| **2** | **Visual Grounding** | `backend/pipelines/grounding.py`, `apps/web/src/components/map/GeoWorkspace.tsx` | `POST /api/v1/analysis/grounding` | Yes (GeoChat-7B 4-bit) | **PIPELINE VERIFIED**<br>*(Real Model: Weights On-Demand)* | Box parsing $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$, Affine transform, Shapely UTM ground area |
| **3** | **Bi-Temporal Change Detection** | `backend/pipelines/bi_temporal.py`, `backend/models/change/` | `POST /api/v1/analysis/change` | Yes (Siamese ChangeNet) | **REAL MODEL VERIFIED** | `ChangeDetectionNet` PyTorch forward pass, sigmoid tensor $>0.5$, OpenCV contours, UTM $m^2$/ha |
| **4** | **Optical + SAR Corroboration** | `backend/models/dofa/`, `backend/pipelines/optical_sar.py` | `POST /api/v1/analysis/optical-sar` | No (Deterministic Spectral + SAR $\sigma^0$ dB) | **DETERMINISTIC CORROBORATION VERIFIED** | Sentinel-2 spectral divergence vs Sentinel-1 C-band SAR $\sigma^0$ ($-14.5\text{ dB}$) decision concordance |
| **5** | **Agentic Orchestration & Routing** | `backend/agent/router.py`, `backend/agent/orchestrator.py` | `POST /api/v1/query` | No | **PIPELINE VERIFIED** | 3-layer validation, input rejection for invalid asset count, compound temporal+SAR dispatch |
| **6** | **Remote-Sensing Adaptation** | `backend/geospatial/crs.py`, `backend/geospatial/metadata.py` | Core Math Head | No | **PIPELINE VERIFIED** | GDAL/Rasterio GeoTIFF parsing, GSD extraction, CRS inspection, WGS84 to UTM reprojection |
| **7** | **Evidence-Grounded Output & Trace** | `backend/evidence/`, `apps/web/src/components/intelligence/WhyThisAnswer.tsx` | Analysis Payloads | No | **PIPELINE VERIFIED** | Canonical Evidence Object linking claims, model used, geographic coordinates, execution step trace |
| **8** | **Interactive Scientific GUI** | `satquery-ai/apps/web/` | `http://localhost:3000` | No | **DEMO & PIPELINE VERIFIED** | 60–65% map hero, finding ↔ evidence ↔ geography linking, temporal slider, multi-step agent animation |
| **9** | **GeoTIFF / TIFF Multi-Band Ingestion** | `backend/geospatial/metadata.py`, `backend/storage/preview.py` | `POST /api/v1/images/inspect` | No | **PIPELINE VERIFIED** | Multi-band statistics, nodata masking, 2nd–98th percentile dynamic contrast stretch PNG preview |
| **10** | **Multi-Format Export Dossiers** | `backend/reports/generator.py`, `apps/web/src/components/ReportExportModal.tsx` | `GET /api/v1/reports/{job_id}/{format}` | No | **PIPELINE VERIFIED** | ReportLab PDF mission dossier, RFC 7946 GeoJSON spatial polygons, CSV tabular area metrics |

---

## 3. SIH Submission Readiness Assessment
- **Software & Systems Engineering**: READY ✅
- **Deterministic Geospatial & GIS Computation**: READY ✅
- **Agentic Multi-Step Orchestration**: READY ✅
- **Siamese ChangeNet Neural Inference**: READY ✅
- **Optical + SAR Corroboration Engine**: READY ✅
- **GeoChat-7B 4-bit VLM**: READY WITH ON-DEMAND WEIGHT DOWNLOAD PROTOCOL ⚠️
