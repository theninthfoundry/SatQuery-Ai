# SatQuery AI — Master System & 8-Gate Delivery Report

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology theme**  
**Official Title:** *"SatQuery AI — An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries"*  
**Constraint Envelope:** ₹0 budget · Single NVIDIA RTX 4060 Laptop (8 GB VRAM) · Pure Python + FastAPI + Next.js · Offline-capable

---

## Executive Summary

SatQuery AI has been built end-to-end according to the **Master PRD v1.0** and **8-Gate Milestone Plan**. The system is an agentic vision-language assistant that strictly adheres to the **Orchestrator vs. Calculator** architectural principle:
- **AI orchestrates**: Routes natural-language queries to deterministic perception specialists.
- **Scientific tools compute**: GDAL, Rasterio, Shapely, PyProj, and Neural Encoders compute exact areas ($m^2$), bounding polygons, and spectral/radar metrics.
- **Evidence Engine audits**: Produces structured provenance traces and calculates resolution-grounded confidence scores.
- **AI explains**: Synthesizes verified results with zero hallucinations.

---

## 8-Gate Capability Matrix

| Gate | Requirement / Capability | Status | Implemented Module | Verifiable Artifacts |
|---|---|---|---|---|
| **Gate 1** | Geospatial Ingestion & Modality Triage | ✅ **DELIVERED** | `backend/geospatial/`, `backend/storage/` | Multi-band statistics, dynamic contrast percentile previews, CRS inspection |
| **Gate 2** | Single-Image RS VQA | ✅ **DELIVERED** | `backend/models/geochat/`, `backend/pipelines/single_image.py` | GeoChat-7B 4-bit BitsAndBytes adapter, resolution-weighted confidence |
| **Gate 3** | Single-Image Visual Grounding | ✅ **DELIVERED** | `backend/pipelines/grounding.py`, `apps/web/GroundingCanvas.tsx` | Affine coordinate matrix mapping to GeoJSON polygons with area ($m^2$) |
| **Gate 4** | Bi-Temporal Change Detection | ✅ **DELIVERED** | `backend/pipelines/bi_temporal.py`, `apps/web/ChangeViewer.tsx` | Siamese ChangeNet, polygonization, $m^2$ ground area, before/after slider |
| **Gate 5** | Optical + SAR Multimodal Analysis | ✅ **DELIVERED** | `backend/models/dofa/`, `backend/pipelines/optical_sar.py` | DOFA ViT-Base, Sentinel-1 radar backscatter ($\sigma^0$ dB) corroboration |
| **Gate 6** | Agentic Orchestration & Trace | ✅ **DELIVERED** | `backend/agent/`, `apps/web/AgentChatConsole.tsx` | Intent classifier, autonomous pipeline dispatch, live step bubbles |
| **Gate 7** | Multi-Format Report Exporter | ✅ **DELIVERED** | `backend/reports/`, `apps/web/ReportExportModal.tsx` | Downloadable mission dossiers in PDF, GeoJSON, and CSV formats |
| **Gate 8** | Benchmark Harness & Offline Demo | ✅ **DELIVERED** | `backend/evaluation/`, `scripts/run_offline_demo.py` | RSVQA, CDVQA, BigEarthNet, Grounding IoU, and pre-seeded ISRO demo data |

---

## Architecture Blueprint

```
                      +---------------------------------------+
                      |   Next.js 14 Web Console (apps/web)   |
                      |  Dynamic Preview, Slider, Overlay,    |
                      |  Evidence Card, Agent Chat Bar, PDF   |
                      +-------------------+-------------------+
                                          |
                                    REST API (JSON)
                                          |
                      +-------------------v-------------------+
                      |       FastAPI Backend Server          |
                      |          (backend/main.py)            |
                      +-------------------+-------------------+
                                          |
           +------------------------------+------------------------------+
           |                              |                              |
+----------v-----------+      +-----------v----------+      +------------v------------+
|  Agent Orchestrator  |      |   Perception Engine  |      | Evidence & Audit Engine |
|  • router.py         |      |  • GeoChat-7B (4-bit)|      | • confidence.py         |
|  • orchestrator.py   |      |  • Siamese ChangeNet |      | • provenance.py         |
|  • Intent Classifier |      |  • DOFA ViT-Base     |      | • builder.py            |
+----------------------+      +-----------+----------+      +-------------------------+
                                          |
                              +-----------v----------+
                              | Geospatial Math Head |
                              | • Affine Transform   |
                              | • Shapely / PyProj   |
                              | • Real Area Engine m²|
                              +----------------------+
```

---

## Quickstart Instructions

### 1. Launch Offline Demo Mode (Backend + Pre-Seeded ISRO Scenarios)
```powershell
python scripts/run_offline_demo.py
```

### 2. Launch Next.js Web Console
```powershell
cd apps/web
npm install
npm run dev
```
Open **http://localhost:3000** in your browser.

### 3. Run Automated Multi-Phase Test Suite
```powershell
pytest tests/ -v
```
