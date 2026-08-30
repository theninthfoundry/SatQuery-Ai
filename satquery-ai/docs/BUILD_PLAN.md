# SatQuery AI — Build Plan & Milestone Gates (v1.0)

This document establishes the official development sequence, engineering gates, and milestone acceptance criteria for SatQuery AI.

---

## 1. Development Sequence

```text
DATA & GEOSPATIAL ENGINE (Phase 0) ✅
       │
       ▼
SPECIALIST MODELS: Single-Image VQA & Grounding (Phase 1)
       │
       ▼
BI-TEMPORAL CHANGE PIPELINE & AREA ENGINE (Phase 2)
       │
       ▼
OPTICAL-SAR MULTIMODAL FUSION & CORROBORATION (Phase 3)
       │
       ▼
AGENTIC ORCHESTRATION & EVIDENCE/PROVENANCE ENGINE (Phase 4)
       │
       ▼
EVALUATION HARNESS & BENCHMARKS (Phase 5)
       │
       ▼
OFFLINE DEMO & REPORT EXPORTER (Phase 6)
       │
       ▼
PREMIUM COCKPIT UI & FINAL SYSTEM POLISH (Phase 7)
```

---

## 2. Milestone Acceptance Gates

| Gate | Focus Area | Acceptance Criteria | Status |
|---|---|---|---|
| **Gate 1** | **GeoTIFF Ingestion & Metadata** | Upload multi-band GeoTIFF $\rightarrow$ extract affine transform, CRS, resolution, band stats $\rightarrow$ dynamic preview | **PASSED (Phase 0)** |
| **Gate 2** | **Single-Image VQA (GeoChat)** | Upload optical scene $\rightarrow$ ask question $\rightarrow$ GeoChat 4-bit infers grounded text answer $\rightarrow$ evidence created | **Phase 1 Target** |
| **Gate 3** | **Single-Image Visual Grounding** | Natural language referring expression ("Highlight water body") $\rightarrow$ extract bounding box / GeoJSON geometry $\rightarrow$ map overlay | **Phase 1 Target** |
| **Gate 4** | **Bi-Temporal Change & Area** | Before/after pair $\rightarrow$ Siamese network predicts change mask $\rightarrow$ calculate area in $m^2$ and change % $\rightarrow$ CDVQA semantic explanation | **Phase 2 Target** |
| **Gate 5** | **Optical + SAR Multimodal Analysis** | Paired S1 SAR + S2 Optical $\rightarrow$ DOFA feature extraction $\rightarrow$ fusion head $\rightarrow$ cross-modal corroboration score | **Phase 3 Target** |
| **Gate 6** | **Agentic Orchestration & Trace** | Free-form natural language query $\rightarrow$ Agent plans and selects correct tools $\rightarrow$ observable step-by-step execution trace | **Phase 4 Target** |
| **Gate 7** | **Evidence & Confidence Engine** | Full provenance graph generated $\rightarrow$ computed confidence score (no fabricated metrics) $\rightarrow$ downloadable PDF/GeoJSON report | **Phase 4 Target** |
| **Gate 8** | **Offline Standalone Demo** | Entire pipeline runs offline without internet on RTX 4060 $\rightarrow$ zero mock outputs $\rightarrow$ SIH ready | **Phase 6 Target** |

---

## 3. Engineering Rules

1. **No Fake AI**: Never simulate model outputs or hardcode confidence scores. Unimplemented tools must return `NOT_IMPLEMENTED` with `available: False`.
2. **Sequential GPU Execution**: Models are loaded on-demand and evicted with `torch.cuda.empty_cache()` to respect the 8 GB VRAM ceiling.
3. **Deterministic Truth**: Perception models produce masks and numbers; the evidence engine calculates confidence; the LLM only translates verified evidence into natural language.
4. **Observable Provenance**: Every output must link back to specific source imagery, bounding coordinates, model runtime metrics, and execution steps.
