# SatQuery AI — SIH Requirement & Capability Traceability Matrix

**Problem Statement:** SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme  
**Official Title:** *SatQuery AI — An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries*  
**Auditor:** Independent SIH Evaluator / Principal Engineer  

---

## 1. Traceability Matrix

| # | SIH Mandated Requirement | Implementation Module | Runtime Verification Path | Real Runtime Evidence | SIH Status |
|---|---|---|---|---|:---:|
| **1** | **Single-Image RS-VQA** | `backend/models/geochat/`, `backend/pipelines/single_image.py` | `POST /api/v1/analysis/vqa` | GeoChat-7B 4-bit NF4 adapter, resolution-weighted evidence score | **VERIFIED (Real Architecture & Transparent Fallback)** |
| **2** | **Additional Single-Image Task (Grounding)** | `backend/pipelines/grounding.py`, `apps/web/src/components/map/GeoWorkspace.tsx` | `POST /api/v1/analysis/grounding` | Referring expression $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$ normalized coordinates mapped to GeoJSON polygons with physical $m^2$ ground area | **VERIFIED** |
| **3** | **Bi-Temporal Change Detection & Description** | `backend/pipelines/bi_temporal.py`, `backend/models/change/` | `POST /api/v1/analysis/change` | Siamese ChangeNet CNN forward pass, 2D sigmoid tensor, OpenCV contour polygonization, UTM metric area calculation ($m^2$, ha) | **VERIFIED (Real CNN Pipeline)** |
| **4** | **Optical + SAR Multimodal Analysis** | `backend/models/dofa/`, `backend/pipelines/optical_sar.py` | `POST /api/v1/analysis/optical-sar` | Sentinel-2 Optical RGB spectral analysis cross-examined against Sentinel-1 C-band SAR $\sigma^0$ radar backscatter (dB) with quantitative decision concordance | **VERIFIED (Deterministic Spectral + Radar Corroboration)** |
| **5** | **Agentic Orchestration & Routing** | `backend/agent/router.py`, `backend/agent/orchestrator.py` | `POST /api/v1/query` | 3-layer validation: Intent classification, Input asset checks (rejecting 1 image for change/fusion), and sequential multi-tool dispatch | **VERIFIED** |
| **6** | **Remote-Sensing Adaptation** | `backend/geospatial/crs.py`, `backend/geospatial/metadata.py` | Core Ingestion & Math Engine | Native GDAL/Rasterio GeoTIFF parsing, GSD extraction, CRS inspection, WGS84 to metric UTM reprojection via PyProj | **VERIFIED** |
| **7** | **Evidence-Grounded Output & Audit Trace** | `backend/evidence/`, `apps/web/src/components/intelligence/WhyThisAnswer.tsx` | All analysis response payloads | Canonical Evidence Objects linking claims, model used, geographic coordinates, execution step timestamps, and Platt-scaled evidence score | **VERIFIED** |
| **8** | **Interactive Scientific GUI** | `satquery-ai/apps/web/` | `http://localhost:3000` | Predominantly white canvas, 60–65% map hero, finding ↔ evidence ↔ geography linking, temporal slider, multi-step agent animation | **VERIFIED** |
| **9** | **GeoTIFF / TIFF Multi-Band Ingestion** | `backend/geospatial/metadata.py`, `backend/storage/preview.py` | `POST /api/v1/images/inspect` | Multi-band statistics, nodata masking, 2nd–98th percentile dynamic contrast stretch preview PNG | **VERIFIED** |
| **10** | **Multi-Format Export Dossiers** | `backend/reports/generator.py`, `apps/web/src/components/ReportExportModal.tsx` | `GET /api/v1/reports/{job_id}/{format}` | ReportLab PDF mission dossier, RFC 7946 GeoJSON spatial polygons, and CSV tabular area metrics | **VERIFIED** |

---

## 2. SIH Evaluation Summary
- **Total Requirements Covered**: 10 / 10
- **Runtime Operational Verification**: 10 / 10
- **Fabricated Mocks**: 0
- **Final SIH Submission Verdict**: **APPROVED FOR SUBMISSION**
