# SatQuery AI — Model Strategy & Specialist Architecture (v1.0)

This document formalizes the AI model specialization, multimodal EO representation architecture, runtime memory strategy, and evaluation benchmarks for SatQuery AI.

---

## 1. Core Architectural Principle: Specialist Separation

> **"Models produce evidence. The agent selects models. The evidence engine determines confidence. The language model only explains verified results."**

The LLM is **never** permitted to calculate scientific results or fabricate confidence. It functions strictly as an orchestrator and translator of deterministic evidence.

```text
USER QUESTION
      │
      ▼
INTENT ROUTER (Deterministic Rules / Small Local LLM)
      │
 ┌────┴───────────────────────────┬───────────────────────────┐
 ▼                                ▼                           ▼
VQA / GROUNDING              CHANGE ENGINE             SAR CORROBORATOR
(GeoChat 4-bit)             (Siamese / CDVQA)           (DOFA / Backscatter)
 │                                │                           │
 └────────────────────────────────┼───────────────────────────┘
                                  ▼
                         DETERMINISTIC FACTS
             (change %, area m², bounding boxes, masks)
                                  │
                                  ▼
                           EVIDENCE ENGINE
                 (Provenance Graph, Computed Confidence)
                                  │
                                  ▼
                           EXPLAINER / UI
              (Grounding Overlay, Map, Grounded Response)
```

---

## 2. Specialist Model Stack

| Component | Selected Model | Primary Role | Target Precision & Runtime |
|---|---|---|---|
| **Query / Language / Grounding** | **GeoChat-7B** | Single-image VQA, scene understanding, visual grounding, referring expressions | 4-bit NF4 / BitsAndBytes (`device_map="auto"`, on-demand VRAM) |
| **Pixel-Level Grounding Fallback** | **GeoPixel** | High-resolution pixel-level grounding if GeoChat bounding is insufficient | 4-bit / Sequential GPU |
| **Multimodal EO Representation** | **DOFA (ViT-Base)** | Sensor-aware visual feature backbone (Sentinel-1 SAR + Sentinel-2 optical) | FP16, frozen backbone + lightweight task adapter |
| **Bi-temporal Change Perception** | **Siamese Change Detector** | Pixel-level difference segmentation, change mask, polygon generation | FP16 / FP32 (<0.8 GB VRAM) |
| **Change Semantics / Change VQA** | **CDVQA** | Semantic interpretation of detected change areas | Sequential execution |
| **Cross-Modal Optical + SAR** | **DOFA Dual-Branch + Fusion Head** | Extracting complementary optical and SAR information | FP16, lightweight MLP / cross-attention head |
| **Intent Routing & Orchestration** | **Deterministic Router + Ollama** | Tool selection and JSON parameter extraction | CPU / Fast offline execution |
| **Evidence & Confidence** | **SatQuery Evidence Engine** | Provenance tracking, audit trails, computed confidence | Deterministic Python / PostGIS |

---

## 3. Detailed Component Breakdown

### A. GeoChat (Single-Image VQA & Grounding)
- **Role**: Primary single-image vision-language model.
- **Capabilities**: Remote-sensing VQA, visual grounding (bounding boxes/regions), scene classification, grounded dialogue.
- **Hardware Strategy**: Official weights trained on A100s will **not** be fine-tuned locally. At runtime on the 8 GB RTX 4060, GeoChat is loaded in **4-bit NF4 quantization (~4.0 - 4.5 GB VRAM)** and unloaded immediately after inference.

### B. DOFA (Dynamic Optical-SAR Foundation Model)
- **Role**: Visual EO representation specialist across varying spectral bands and sensors (Sentinel-1 SAR, Sentinel-2 Optical, NAIP RGB).
- **Nuance**: DOFA provides dynamic wavelength-conditioned feature embeddings, **not** natural-language text generation.
- **Hardware Strategy**: Use DOFA ViT-Base with frozen weights, training only a lightweight task adapter or fusion head on consumer GPU.

### C. Change Perception vs. Change Semantics
We separate the change pipeline into two verifiable steps:
1. **Perception**: Siamese network computes the change probability map, thresholded binary mask, connected components, and geospatial area ($m^2$).
2. **Semantics**: CDVQA / GeoChat receives the verified mask and bounding regions to explain *what* the change represents (e.g., "new urban construction on previously vegetated land").

---

## 4. Benchmark & Evaluation Resources

Evaluation datasets are separated from training/adaptation pipelines:

1. **BigEarthNet.txt**: Large-scale adaptation resource containing 464,044 co-registered Sentinel-1/Sentinel-2 pairs and 9.6M text annotations for multimodal representation.
2. **VRSBench**: 29,614 high-resolution images, 52,472 object references, and 3.1M+ VQA pairs for visual grounding and VQA evaluation.
3. **RSVQA (HR & LR)**: Standard benchmark for remote sensing VQA evaluation.
4. **CDVQA**: Standard benchmark for change-detection visual question answering.
5. **ISRO/SAC Official Evaluation Set**: Pre-georeferenced Cartosat-2S optical + RISAT SAR pairs.

---

## 5. Fallback Hierarchy (Zero Single Points of Failure)

```text
VQA:
  GeoChat-7B (4-bit) ──► Quantized Compact VLM ──► Structured RS Classifier Fallback

Grounding:
  GeoChat Grounding ──► GeoPixel ──► Classical Object Detector / Contours

Change Detection:
  Trained Siamese Network ──► ChangeFormer ──► Classical Spectral Difference (NDVI / Log-Ratio)

Optical + SAR:
  DOFA Feature Fusion ──► Dual-Encoder Concat ──► Independent Optical + SAR Cross-Check

Orchestration:
  Ollama Local LLM ──► Strict JSON Schema Validator ──► Deterministic Regex Router
```
