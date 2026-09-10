# SatQuery AI — Authoritative Implementation Truth Matrix

**Classification Standard**:
- `NOT_IMPLEMENTED`: Architectural target; no runtime code.
- `IMPLEMENTED`: Code exists, not integrated end-to-end.
- `INTEGRATED`: Connected into pipelines and endpoints.
- `EXECUTABLE`: Fully executable without mock data or synthetic stubs.
- `VALIDATED`: Verified with rigorous unit/integration tests and real raster fixtures.
- `BENCHMARKED`: Quantitatively evaluated against reproducible test splits.

---

## 1. System Truth Matrix

| Subsystem / Capability | Status | Execution Path | Real Data Required | Real Model Required | Truth State & Fallback Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Raster Ingestion & Metadata** | `VALIDATED` | `backend/geospatial/metadata.py` | Yes (GeoTIFF, PNG, JPEG) | No | Strict path validation, format sniff, bounds reprojection to WGS84. |
| **AOI Importer** | `VALIDATED` | `backend/geospatial/aoi_importer.py` | Yes (.geojson, .kml, .kmz, .shp.zip) | No | Zip Slip protection, topological repair (`buffer(0)`), geodesic WGS84 area/perimeter. |
| **STAC Discovery** | `VALIDATED` | `backend/ingestion/stac_client.py` | Yes (Live STAC / Offline cache) | No | Live query (Earth Search) with explicit offline fallback disclosure. |
| **Pixel Microscope Inspector** | `VALIDATED` | `backend/api/routes/images.py` | Yes (Multiband raster) | No | Inverse affine sampling, band reflectances, NDVI/NDWI/NDBI, GSD, T1↔T2 deltas. |
| **Zonal Statistics** | `VALIDATED` | `backend/api/routes/images.py` | Yes (Raster + Polygon) | No | Rasterio geometry masking, count, min, max, mean, median, std, p25, p75, p95. |
| **Multi-Epoch Timeline** | `VALIDATED` | `backend/api/routes/images.py` | Yes (Image records) | No | 4–12 observation epochs with dates, platforms, cloud coverage, and resolutions. |
| **Co-Registration Engine** | `VALIDATED` | `backend/geospatial/registration.py` | Yes (Bitemporal pair) | No | AKAZE/ORB keypoints, RANSAC homography, RMSE pixels/meters, inlier ratio. |
| **Siamese ChangeNet** | `VALIDATED` | `backend/models/change/` | Yes (Bitemporal rasters) | Untrained Baseline | Honest disclosure: untrained weights emit warning; classical spectral delta backup. |
| **SAR Radiometric Calibrator** | `VALIDATED` | `backend/geospatial/sar_processor.py` | Yes (Sentinel-1 SAR) | Deterministic Physics | Radiometric σ⁰ dB calibration, Lee 5x5 speckle filter, adaptive urban threshold. |
| **Multimodal Corroboration** | `VALIDATED` | `backend/engines/fusion.py` | Yes (Optical + SAR) | No | Level 2 spatial consensus (IoU, consensus area, discordance diagnosis). |
| **Evidence Gate** | `VALIDATED` | `backend/evidence/gate.py` | Yes (Pipeline outputs) | No | Epistemological policy: ANSWER / QUALIFY / ABSTAIN based on 5 reliability factors. |
| **Canonical EvidenceContract**| `VALIDATED` | `backend/evidence/contract.py` | Yes (Complete mission metadata) | No | Strict 21-field canonical schema; zero frontend fabrication permitted. |
| **Audit Dossier Reporting** | `VALIDATED` | `backend/reports/` | Yes (EvidenceContract) | No | ReportLab PDF, RFC 7946 GeoJSON, CSV metrics, canonical JSON. |
| **Analysis Replay Engine** | `VALIDATED` | `scripts/reproduce_analysis.py` | Yes (Analysis ID / Manifest) | No | Bitwise input/model/parameter validation; emits REPRODUCED / DIFFERENT / FAILED. |
| **Model Registry & Manifest** | `VALIDATED` | `scripts/verify_models.py` | Checkpoints on disk | Yes (Torch) | Real weights verification; produces `models_manifest.json` with truth states. |
| **19-Stage Golden Mission** | `VALIDATED` | `scripts/run_golden_mission.py` | Yes (T1, T2, SAR) | Untrained Baseline | Complete vertical slice execution; 100% reproducible area metrics. |
| **Frontend UI (Scientific)** | `VALIDATED` | `apps/web/` | Yes (FastAPI backend) | No | One Screen. Four Concepts (Ask, See, Understand, Verify); zero clutter. |

---

## 2. Hardening Purge Verification

1. **Synthetic Trigonometric Coordinates**: Completely removed from all production routes and seed scripts.
2. **Fabricated Confidence Scores**: Zero default floats (0.94, 0.96) remain. All confidence values originate from deterministic factors or calibrated model outputs.
3. **Frontend Mock Routes**: `apps/web/src/app/api/v1` completely purged. Next.js proxies all API requests directly to FastAPI backend via rewrites.
4. **Untrained Weight Disclosure**: When running without trained LEVIR-CD weights, `is_real_weights: false` and `execution_mode: "classical_fallback"` are strictly reported in API responses and UI cards.
