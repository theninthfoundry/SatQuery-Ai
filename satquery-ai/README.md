# SatQuery AI — Vision-Language Assistant for Multimodal Remote Sensing

**Smart India Hackathon (SIH 2024 / SIH26167) · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
*An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Natural-Language Text Queries*

---

## 1. System Overview

SatQuery AI is an agentic Earth Observation analysis platform engineered to bridge natural-language inquiries and complex remote sensing operations. Rather than serving as a generic chatbot, SatQuery combines specialized neural perception heads, deterministic geospatial computation, and an auditable evidence engine to answer complex satellite queries with grounded geometric proof.

### Core Architectural Pillars
1. **Remote-Sensing Vision-Language Analysis**: Powered by GeoChat-7B (4-bit BitsAndBytes NF4 quantization) for descriptive land cover visual question answering and text-guided referring expression visual grounding.
2. **Geospatial & Projection Computation**: Native GDAL/Rasterio/PyProj geodetic engine converting pixel coordinates to exact WGS84 and metric projected UTM polygons ($m^2$, ha).
3. **Bi-Temporal Surface Change Detection**: Siamese ChangeNet dual-branch convolutional neural network producing 2D probability tensors and topological contour vector polygons.
4. **Optical + SAR Corroboration**: Cross-modal decision concordance evaluating optical spectral divergence (RGB / NDWI) alongside Sentinel-1 C-band SAR radar backscatter intensity ($\sigma^0$ in dB).
5. **Evidence & Provenance Graph**: Canonical, reproducible evidence dossiers with millisecond-level execution traces and multi-factor Evidence Scores.
6. **3-Layer Agentic Orchestrator**: Intent classification, spatial asset validation, and multi-step workflow dispatch capable of compound multi-modal analysis.

> [!IMPORTANT]
> **Neural Checkpoint Activation & Transparent Offline Protocol:**  
> Large neural specialist checkpoints (such as GeoChat-7B 4-bit) are activated on demand via `python scripts/download_geochat.py`. When full model weights are not resident, SatQuery enters an explicitly labeled offline fallback mode (`fallback_used: true`, `is_real_weights: false`) and **never represents fallback output as genuine neural-model inference**.

---

## 2. Quick Start & One-Click Launch

### Single Reproducible Command
```powershell
# Windows
.\start.ps1
```

```bash
# Linux / macOS
./start.sh
```

The launcher automatically:
- Provisions SQLite tables and image asset storage directories.
- Seeds canonical demonstration scenarios (*Bangalore Urban Expansion*, *Brahmaputra Flood Dynamics*, *Sundarbans Mangrove Delta*, *Thar Canal*).
- Starts the FastAPI backend at `http://127.0.0.1:8000`.
- Launches the Next.js 14 scientific console at `http://localhost:3000`.

---

## 3. Five Canonical Verification Missions

| Mission | Type | Natural-Language Query | Primary Execution Flow |
|---|---|---|---|
| **01** | **RS-VQA** | *"Describe the dominant land cover and major objects visible in this image."* | 3-Layer Router (`vqa`) → GeoChat Specialist → Land Cover Assessment + Evidence Card |
| **02** | **Grounding** | *"Where is the largest water body?"* | Router (`grounding`) → GeoChat BBox $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$ → Affine Geotransform → Shapely Metric UTM Area ($m^2$, ha) |
| **03** | **Temporal Change** | *"What changed between these two observations and where?"* | $T_1 + T_2$ → ORB/RANSAC Alignment → Siamese ChangeNet CNN → 2D Sigmoid Tensor ($>0.5$) → OpenCV Contours → Map Red Clusters (`01`, `02`) |
| **04** | **Optical + SAR** | *"Use both images together to identify regions that are likely built-up."* | Optical S2 + SAR S1 → DOFA Specialist → Spectral Index vs $\sigma^0$ dB Backscatter ($-14.5\text{ dB}$) → Decision Concordance Score |
| **05** | **Compound Query** | *"Has the built-up area increased between the two dates? Use the optical and SAR observations to corroborate the result and report the total changed area in hectares."* | **Multi-Model Orchestration**: ChangeNet temporal pipeline + DOFA Optical/SAR corroboration → $2.56\text{ ha}$ ($25,600\text{ m}^2$) alteration + SAR verification + 1-click PDF/GeoJSON/CSV exports |

---

## 4. Hardware Envelope & Performance Profile

- **Target Device**: Single NVIDIA RTX 4060 Laptop GPU (8 GB VRAM budget).
- **Sequential Memory Eviction**: `gpu_manager.unload_active()` unloads inactive models via PyTorch CUDA cache clearing, enforcing a peak VRAM footprint of **$<4.65\text{ GB}$**.
- **Average Pipeline Latency**: $380\text{ ms} - 750\text{ ms}$ for complete end-to-end multi-step analysis.

---

## 5. Documentation Directory

- [`docs/FINAL_TRUTH_MATRIX.md`](docs/FINAL_TRUTH_MATRIX.md) — Color-coded capability verification matrix.
- [`docs/SIH_FINAL_TRACEABILITY.md`](docs/SIH_FINAL_TRACEABILITY.md) — Traceability matrix covering all 10 SIH requirements.
- [`docs/METHODOLOGY_AND_SIH_VERIFICATION.md`](docs/METHODOLOGY_AND_SIH_VERIFICATION.md) — Mathematical formulas and 5-Mission proofs.
- [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) — Reproduction guide for external evaluators.
- [`docs/FINAL_RELEASE_AUDIT.md`](docs/FINAL_RELEASE_AUDIT.md) — Complete forensic audit and sign-off report.

---

## 6. License & Attribution

Developed for **Smart India Hackathon 2024 · Problem Statement SIH26167 · Indian Space Research Organisation (ISRO)**.  
Released under the Apache 2.0 License.
