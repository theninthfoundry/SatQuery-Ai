# SatQuery AI — Phase 1: Comprehensive Repository & Scientific Audit

**Audit Date:** 2026-08-31  
**Target Environment:** Single NVIDIA RTX 4060 Laptop (8 GB VRAM) · Pure Python / PyTorch / FastAPI / Next.js

---

## 1. Executive Summary & Capability Classification Matrix

Every claimed capability in the repository has been audited and classified into exactly one of:
- **`REAL`**: Genuine mathematical/computational execution without mocks or placeholders.
- **`PARTIAL`**: Real architecture and code present, but missing weights or containing a pipeline discontinuity.
- **`SCAFFOLD`**: Interface and adapter structure defined, but currently running on fallback or heuristic paths.
- **`DEMO/FALLBACK`**: Pre-seeded demo scripts or hardcoded static metric reports.
- **`BROKEN`**: Code containing syntax or logical execution failures.

| Component / Subsystem | Path | Classification | Detailed Audit Finding |
|---|---|---|---|
| **Geospatial & Ingestion Engine** | `backend/geospatial/`, `backend/storage/` | **`REAL`** | Real GDAL/Rasterio parsing, CRS/EPSG extraction, windowed radiometry statistics, 2%–98% percentile PNG preview generation, and affine coordinate transforms. |
| **Ground Area & Geometry Engine** | `backend/geospatial/geometry.py`, `backend/pipelines/grounding.py` | **`REAL`** | Real Shapely & PyProj polygon coordinate projection, UTM transformation, and physical area calculation in square metres ($m^2$) and hectares. |
| **GeoChat-7B Model Adapter** | `backend/models/geochat/` | **`SCAFFOLD`** | BitsAndBytes 4-bit loading architecture is coded, but no weights exist on disk (`./checkpoints/geochat/` is empty). `vqa()` and `ground()` execute fallback strings and keyword heuristics. |
| **Siamese ChangeNet** | `backend/models/change/` | **`PARTIAL`** | Real PyTorch Siamese CNN (`ChangeDetectionNet`) and tensor inference logic exist. However, weights are untrained (random initialization) and `bi_temporal.py` had a pipeline flaw synthesizing a center box. |
| **DOFA Foundation Adapter** | `backend/models/dofa/` | **`SCAFFOLD`** | DOFA ViT-Base checkpoint is missing. Feature extraction runs numpy spectral averages and heuristic radar backscatter thresholds (`< -20 dB`) rather than the transformer backbone. |
| **Single-Image VQA Pipeline** | `backend/pipelines/single_image.py` | **`PARTIAL`** | Full image retrieval, database audit logging, and evidence building are REAL, but VLM output is from GeoChat fallback string. |
| **Visual Grounding Pipeline** | `backend/pipelines/grounding.py` | **`PARTIAL`** | Affine coordinate transform and GeoJSON polygon generation are REAL, but input bounding boxes are produced by keyword heuristics in `geochat.ground()`. |
| **Bi-Temporal Change Pipeline** | `backend/pipelines/bi_temporal.py` | **`PARTIAL`** | Spatial overlap IoU, real-world area calculation ($m^2$/ha), and mask overlay generation are REAL; requires connecting raw 2D probability tensor from ChangeNet. |
| **Optical + SAR Pipeline** | `backend/pipelines/optical_sar.py` | **`PARTIAL`** | Multi-sensor database retrieval and cross-modal evidence formatting are REAL; features are extracted via numpy proxies rather than DOFA embeddings. |
| **Agent Router & Orchestrator** | `backend/agent/router.py`, `orchestrator.py` | **`REAL`** | Deterministic intent classification (VQA, Grounding, Change, Optical+SAR) and autonomous toolchain dispatch graph work as designed. |
| **Evidence & Confidence Engine** | `backend/evidence/confidence.py`, `builder.py` | **`PARTIAL (HEURISTIC)`** | Structured evidence objects and execution provenance steps are REAL. Confidence calculation is a deterministic linear heuristic (70% model + 30% GSD), **not** an empirical calibrated probability. |
| **Report Exporter (PDF/GeoJSON/CSV)** | `backend/reports/generator.py` | **`REAL`** | Real PDF stream generation, real GeoJSON FeatureCollection serialization, and real CSV tabular export. |
| **Benchmark Evaluation Harness** | `backend/evaluation/harness.py` | **`DEMO / MOCK`** | Returns hardcoded static numbers (`84.6%`, `71.8%`, `86.2%`, `91.4%`) without loading or evaluating actual test datasets. |
| **Offline Demo Seeder** | `scripts/seed_demo_data.py` | **`REAL`** | Generates real multi-band GeoTIFFs, populates SQLite/Postgres records, and renders previews. |

---

## 2. Detailed Findings by Model & Pipeline

### A. GeoChat-7B (`backend/models/geochat/adapter.py`)
* **Expected Checkpoint:** `MBZUAI/geochat-7b` from Hugging Face (~14 GB in FP16 / ~4.5 GB in 4-bit NF4).
* **Current State:**
  * Lines 92–113 contain valid Hugging Face `AutoModelForCausalLM` loading code with `BitsAndBytesConfig(load_in_4bit=True)`.
  * Because `./checkpoints/geochat/` does not exist locally, `is_checkpoint_available()` returns `False`.
  * `vqa()` returns template string: `"[GeoChat-7B Ready] VQA request for '{question}' on image '{img_p.name}' received."`
  * `ground()` uses keyword matching:
    ```python
    if "water" in referring_expression.lower():
        boxes.append({"ymin": 0.20, "xmin": 0.30, "ymax": 0.65, "xmax": 0.75})
    ```
* **Required Action:** Download model weights (or quantized GGUF/AWQ/BitsAndBytes weights) to `./checkpoints/geochat` and wire `model.generate()`.

---

### B. Siamese ChangeNet (`backend/models/change/`)
* **Architecture:** `ChangeDetectionNet` (in `backend/models/change/model.py`) is a genuine PyTorch Siamese CNN with 4 convolutional downsampling blocks, absolute difference + concatenation feature fusion, and a 4-layer convolutional decoder.
* **Current State:**
  * The model class and inference wrapper `ChangeDetector` are 100% real PyTorch code.
  * In the absence of `checkpoints/best.pt`, it runs with initialized weights (untrained baseline).
  * **Pipeline Issue in `bi_temporal.py` (Lines 251–257):**
    ```python
    # Flaw: Generated a synthetic square instead of using ChangeDetector output
    mask_arr = np.zeros((256, 256), dtype=np.uint8)
    if change_percent > 0:
        r = int(np.sqrt((change_percent / 100.0) * (256 * 256)))
        mask_arr[128 - r // 2 : 128 + r // 2, 128 - r // 2 : 128 + r // 2] = 255
    ```
* **Required Action:** Modify `ChangeDetector.detect()` to return the raw 2D numpy mask array `probs > threshold` and pass it directly into `mask_to_geographic_polygons()`.

---

### C. DOFA Foundation Adapter (`backend/models/dofa/adapter.py`)
* **Expected Checkpoint:** DOFA ViT-Base (`zhu-xlab/DOFA` GitHub / Hugging Face).
* **Current State:**
  * Extracts numpy-level image statistics:
    * Optical: Mean RGB values and basic spectral difference proxy (`b > r + 15`).
    * SAR: Mean radar backscatter dB from raster band 1, checking fraction of low backscatter pixels (`< -20 dB`).
  * Cross-modal agreement score is computed as `1.0 - abs(opt_water - sar_water) * 2.0`.
* **Required Action:** Maintain this as an explicit **Sensor-Proxy Corroboration Engine** or connect the DOFA ViT-Base feature extractor when downloaded.

---

### D. Evidence & Confidence Engine (`backend/evidence/confidence.py`)
* **Current State:**
  * Confidence is calculated deterministically via:
    $$\text{Confidence}_{\text{VQA}} = 0.70 \times \text{ModelScore} + 0.30 \times \text{ResolutionScore}(\text{GSD})$$
    $$\text{Confidence}_{\text{Multimodal}} = 0.45 \times \text{Model} + 0.30 \times \text{Registration} + 0.15 \times \text{SAR} + 0.10 \times \text{Resolution}$$
  * Resolution scoring is a step function (1.0 for GSD $\le 1\text{m}$, 0.90 for $10\text{m}$, 0.75 for $30\text{m}$).
* **Scientific Labeling:** This is a **heuristic confidence index**, not an empirical probability.

---

### E. Benchmark Evaluation Harness (`backend/evaluation/harness.py`)
* **Current State:**
  * `evaluate_rsvqa()`, `evaluate_grounding()`, `evaluate_cdvqa()`, and `evaluate_bigearthnet_corroboration()` currently return static hardcoded variables (`84.6`, `71.8`, `86.2`, `91.4`).
* **Required Action:** Replace hardcoded returns with dataset loading scripts that iterate over sample image-question pairs and calculate real Exact Match, Accuracy, BLEU, and IoU.

---

## 3. Immediate Action Plan for Phase 1 Activation

1. **Fix ChangeNet Pipeline Discontinuity:** Update `backend/models/change/infer.py` and `backend/pipelines/bi_temporal.py` so the raw 2D prediction mask from PyTorch is polygonized.
2. **Download & Activate GeoChat-7B in 4-bit:** Implement standalone download script and activate 4-bit BitsAndBytes sequential loading on GPU.
3. **Build Real Ground-Truth Benchmark Evaluator:** Replace static numbers in `backend/evaluation/harness.py` with real evaluation over test sample JSONs.
