# SatQuery AI — Master PRD v1.0

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology theme**
**Official title:** *"SatQuery AI — An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries"* (confirmed against the public SIH 2026 problem statement catalogue)
**Constraint envelope:** ₹0 budget · single RTX 4060 laptop (assume 8 GB VRAM) + i7 CPU · offline-capable · SIH-timeline realistic

---

## 0. Read This First — Reality Check

Before any architecture, three honest calibrations, because a PRD that only reassures you is worse than useless three weeks before a demo:

1. **The official title says "Vision-Language Assistant," not "fusion research platform."** The breadth you've been planning against (VQA + a second single-image task + multitemporal change + optical/SAR paired analysis + agentic orchestration) is real, but I don't have the full official PS text with the exact dataset schema and grading rubric in front of me — only the confirmed title/theme/sponsor. Treat every dataset-name and benchmark-detail assumption below as **provisional until you paste in the actual official PDF text**. This is flagged again in Open Questions.
2. **True optical–SAR deep fusion is a research problem, not a hackathon feature.** Paired, well-registered optical/SAR fusion models are scarce even in academia. The defensible move is to build **cross-modal corroboration** (two independent, simpler analyses that agree or disagree) and say exactly that to a judge — not to claim a fusion model you don't have. Judges at ISRO-sponsored PS tables often include people who can tell the difference; honesty here is a *strength*, not a weakness.
3. **An 8 GB laptop GPU cannot hold a VLM + a segmentation model + a change-detection model + an LLM all resident at once.** Your architecture has to sequence model loading, use small/quantized models, or lean on a free-tier API when online. "Runs entirely local" and "runs a 7B VLM plus four other models simultaneously" are in tension — pick which one you're actually promising.

None of this kills the project. It reframes the win condition: **the differentiator is the agent + evidence layer wrapped around honestly-scoped perception models — not a bigger model.**

---

## 1. Problem Statement

Remote-sensing analysts currently need domain expertise plus a manual multi-tool pipeline (image discovery → preprocessing → model selection → interpretation → reporting) to answer a simple question about Earth-observation imagery. SatQuery AI's job is to let a non-expert ask a natural-language question about optical and SAR imagery and receive an answer that is **grounded** (points at the pixels that justify it), **quantified** (numbers, not vibes), and **auditable** (shows which models/data produced the number).

**Who this serves (for the demo):** a SIH jury evaluating against the official rubric, standing in for the real end user — an agriculture/disaster-response/urban-planning analyst who currently has no way to query EO imagery without remote-sensing training.

---

## 2. Product Vision (one sentence)

> Ask Earth a question in plain language. Get a grounded, evidence-backed answer — not a chat transcript.

**Explicit anti-pattern:** do not build "ChatGPT with an image attached." The differentiator is that every answer traces back to a specific model run, on specific pixels, with a computed (not invented) confidence score.

---

## 3. Goals (what "done" looks like)

| # | Goal | How you'll know |
|---|------|------------------|
| G1 | Answer single-image questions about a scene | ≥1 working VQA path, constrained-vocabulary fallback if open VQA underperforms |
| G2 | Perform one additional single-image analytical task | Working object/building detection or land-cover segmentation with a visible mask/box output |
| G3 | Detect and quantify change between two dated images of the same AOI | Change % + changed-region polygons rendered on a map |
| G4 | Cross-check optical findings against SAR when both are available | A visible "corroboration" score, computed from real signal, not hardcoded |
| G5 | Route natural-language questions to the right capability automatically | Agent correctly selects VQA vs. change vs. corroboration path without the user picking a mode |
| G6 | Every answer is explainable | "Why?" click reveals source imagery, model used, and confidence breakdown |
| G7 | Demo survives with no internet | A cached fallback path produces the same UI experience offline |

---

## 4. Non-Goals (say these out loud to your team — this is what stops scope creep)

- **Not** training a foundation VLM from scratch. Use existing open models; your novelty is orchestration + evidence, not model research.
- **Not** solving general open-domain optical–SAR fusion. You are building corroboration, explicitly labeled as such.
- **Not** building cloud infrastructure (Kubernetes, managed DB, autoscaling). One laptop, one FastAPI process, local Postgres.
- **Not** a pixel-perfect co-registration pipeline for arbitrary imagery. Rely on pre-registered pairs where the dataset provides them; if you must register images yourself, use a simple keypoint-matching approach and cap how much engineering time goes here (time-box it, per the scope-creep rule below).
- **Not** a fully general chat UI with unlimited free-text questions in v1. Support a well-tested set of question *intents* (count objects, classify land cover, detect change, corroborate) plus graceful "I can't answer that confidently" for anything else. A system that admits uncertainty beats one that hallucinates a number.
- **Not** spending the first week on the UI. Perception pipeline first, UI wraps around working outputs (Section 19 enforces this ordering).

---

## 5. Requirements Matrix — official capability → engineering deliverable → priority

| Official capability | Engineering deliverable | Priority | Real risk |
|---|---|---|---|
| Single-image VQA | Constrained-intent VQA (count / identify / classify) over an open VLM or CLIP-style classifier, with template fallback | **P0** | Low — most tractable piece |
| Second single-image task | Building/road detection or land-cover segmentation (pick ONE, pretrained where possible) | **P0** | Low–medium |
| Multitemporal change understanding | Registered-pair change detection (siamese segmentation), quantified area/% change, polygon output | **P0** | Medium — registration quality drives everything downstream |
| Optical/SAR paired analysis | Cross-modal corroboration score (independent SAR-side change proxy vs. optical change mask overlap) | **P1**, degrade gracefully to "insufficient SAR evidence" | **High** — deep fusion is out of scope; don't overclaim |
| Agentic orchestration | Intent classifier + tool-calling controller (local LLM or free-tier API) routing to the above tools | **P0** | Medium — depends on reliable intent parsing, not reasoning depth |
| Evaluation vs. public benchmarks + ISRO/SAC dataset | Whatever the official dataset actually provides — **unconfirmed**, see Open Questions | Blocking | Confirm before building the eval harness |

---

## 6. System Architecture

```
                    USER (chat + map)
                          │
                     QUERY ROUTER  ── intent classification (local LLM / rules)
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   VQA / SINGLE-IMAGE   CHANGE ENGINE     SAR CORROBORATION
   (VLM or CLIP-head)   (siamese seg.)    (backscatter proxy)
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ▼
                  EVIDENCE + CONFIDENCE ENGINE
                  (provenance graph, computed score)
                          │
                          ▼
                 GEOSPATIAL RENDER LAYER
              (GeoJSON → map overlay + report)
```

Two processes only: **FastAPI backend** (agent, models, geo pipeline) and **Next.js frontend** (map, chat, evidence panel). No microservices for a hackathon.

---

## 7. AI/ML Design, Per Capability

### 7.1 VQA (single image)
Open-ended VQA generalizes poorly without heavy fine-tuning. For reliability under demo pressure, do **both**:
- A small set of **structured intents** (count objects of class X, identify dominant land cover, is water present) answered via a lightweight detector/classifier — deterministic, fast, defensible.
- A **fallback open VQA** path via a compact VLM (e.g., a distilled/quantized vision-language model that fits comfortably in 8 GB) for anything outside the structured set, clearly flagged in the UI as "best-effort" with a lower default confidence ceiling.

### 7.2 Second single-image task
Pick building or road detection/segmentation over something novel — public pretrained weights exist (SpaceNet/Massachusetts-buildings-style models), which meaningfully de-risks your timeline versus training from zero.

### 7.3 Change detection
Siamese-encoder change model (the LEVIR-CD / OSCD family of architectures) is the standard, well-documented approach. **Registration is the actual hard part** — if the official dataset ships pre-registered pairs (likely, since ISRO/SAC would need this for their own grading), use them directly and don't build a general registration pipeline. If not, use classical feature-matching (ORB keypoints + homography) and time-box it hard.

### 7.4 Optical–SAR "corroboration" (not "fusion")
Compute two independent signals and report agreement, don't claim a joint model:
- Optical signal: % of AOI flagged as changed by the change-detection mask.
- SAR signal: a simple, explainable proxy — log-ratio of backscatter intensity between the two SAR dates in the same AOI, thresholded.
- Corroboration score = spatial overlap between the two flagged regions. Report the number. If SAR data isn't usable for a given AOI, say "SAR corroboration unavailable" rather than fabricating a score.

### 7.5 Agentic orchestration
The agent's job is **routing and composition**, not reasoning over pixels. Two implementation options, pick one and keep the other as fallback:
- **Local:** small instruct model via Ollama, prompted to emit a JSON tool call (most open models don't have native function-calling APIs — this is prompt-engineered structured output, parsed and validated server-side, not true function calling).
- **Hybrid:** Gemini free tier when online, for higher-quality intent parsing on ambiguous questions; same tool schema either way so the swap is transparent to the rest of the system.

---

## 8. Agent & Tool Registry (schema)

```json
{
  "tool": "detect_change",
  "description": "Detect and quantify change between two co-registered images of the same AOI",
  "input_schema": {
    "image_before_id": "string",
    "image_after_id": "string",
    "aoi_id": "string"
  },
  "output_schema": {
    "change_percent": "float",
    "changed_regions": "GeoJSON FeatureCollection",
    "model_confidence": "float"
  }
}
```

Registry entries: `answer_visual_question`, `detect_objects`, `segment_landcover`, `detect_change`, `sar_corroborate`, `calculate_area`, `generate_evidence`, `generate_report`. Each tool is a plain Python function behind a typed interface — the "agent" is a router that picks which function(s) to call and in what order, then hands structured facts (not raw pixels) to a small LLM that phrases the final sentence. This keeps hallucination surface area small: the model composes language from `{"change_percent": 13.8, "region": "eastern AOI"}`, it doesn't invent the number.

---

## 9. Data & Geospatial Pipeline

```
raw image → cloud/noise check → radiometric normalization →
(registration, if pair not pre-aligned) → AOI extraction/tiling →
model inference → GeoJSON output → map render
```

Stack: GDAL, Rasterio, GeoPandas, Shapely — all free, all local. Verify the projection/CRS of the actual ISRO/SAC data early; a CRS mismatch silently breaks every area calculation downstream and is the single most common geospatial bug.

---

## 10. Evidence & Confidence Engine

**Provenance object** — every claim links to what produced it:

```json
{
  "claim": "Built-up area increased 13.8%",
  "derived_from": {
    "tool": "detect_change",
    "inputs": ["image_2024_id", "image_2026_id", "aoi_7"],
    "model": "change-seg-v1"
  },
  "confidence_breakdown": {
    "model_confidence": 0.91,
    "registration_quality": 0.93,
    "sar_corroboration": 0.82
  },
  "confidence_overall": 0.87
}
```

**Confidence must be computed, not generated by the LLM.** A reasonable formula: weighted average of model softmax/IoU confidence, a registration-quality metric (e.g., keypoint-match residual, inverted and normalized), and cross-modal agreement when SAR is available. When any required input is missing or low-quality, the system should be able to say **"insufficient evidence"** — that's a legitimate, and more trustworthy, answer than a confident-sounding guess.

---

## 11. API Contracts (representative)

```
POST /query            { "aoi_id": str, "question": str } → { answer, evidence_id }
GET  /evidence/{id}     → provenance object (Section 10)
POST /aoi               { geometry: GeoJSON } → { aoi_id }
GET  /analysis/{job_id} → status + result once async jobs are used
POST /report/{aoi_id}   → PDF/GeoJSON export
```

Keep it REST + JSON; you don't need WebSockets unless you want live "agent trace" streaming for the demo (nice-to-have, P1).

---

## 12. Database Schema (concise)

```
aoi(id, name, geometry, created_at)
images(id, aoi_id, sensor[optical|sar], acquisition_date, path, crs)
analysis_jobs(id, aoi_id, tool, status, result_ref, created_at)
changes(id, job_id, geometry, change_type, area_m2, confidence)
evidence(id, claim, derived_from_json, confidence_breakdown_json)
reports(id, aoi_id, generated_at, file_path)
```

PostgreSQL + PostGIS, local, in Docker. No managed database needed for a hackathon build.

---

## 13. Frontend / UX — key screens only

1. **Ask + Map** — chat input alongside a MapLibre view of the AOI.
2. **Timeline** — drag between available dates for the same AOI; triggers change/corroboration on demand.
3. **Evidence panel** — before/after imagery, change mask, confidence breakdown, "Why?" always one click away.
4. **Agent trace** (P1, strong demo value) — a short auditable list of steps taken ("query understood → change tool selected → registration checked → SAR corroboration run"), not raw chain-of-thought.
5. **Report export** — PDF/GeoJSON/CSV of the current analysis.

Build these *after* the pipeline in Section 7 produces real outputs — wiring a beautiful UI to a stub is the classic hackathon trap the earlier notes already flagged, and it's worth repeating here as a hard rule.

---

## 14. Model & Dataset Strategy

| Capability | Public dataset options for pretraining/testing | Notes |
|---|---|---|
| VQA | RSVQA | Remote-sensing-specific VQA benchmark |
| Building/road detection | SpaceNet, Massachusetts Buildings | Pretrained weights widely available |
| Change detection | LEVIR-CD, OSCD | OSCD uses Sentinel-2, a reasonable optical proxy if Cartosat-specific pretraining isn't feasible in time |
| Optical–SAR pairs | SEN12MS, SEN1-2 | Useful for building/testing the corroboration logic even before the official ISRO/SAC pairs are available |

Fine-tune via LoRA/PEFT where needed rather than full fine-tunes — far more forgiving on an 8 GB card and on your remaining time budget.

---

## 15. Evaluation Framework / Success Metrics

- VQA: accuracy on held-out structured-intent questions.
- Detection/segmentation: IoU / F1.
- Change detection: F1 or Kappa against labeled change masks.
- Corroboration: agreement rate between optical and SAR signals on a labeled subset (even a small hand-labeled set is enough for a demo-credible number).
- Agent: intent-routing accuracy (did it call the right tool for the right question) — this is a simple, high-value metric that's easy to compute and easy to show a judge.

---

## 16. Reliability & Failure Handling

- **Offline demo mode**: a pre-cached set of AOIs + precomputed results, switchable without changing the UI, for when venue Wi-Fi fails (very common at SIH).
- Explicit "insufficient evidence" response path (Section 10) instead of forced confident answers.
- Input validation on AOI/date mismatches before calling any model.
- If using a free-tier API (Gemini) as a fallback, handle rate-limit/auth failures by falling back to the local model rather than surfacing an error to the judge.

---

## 17. Repository Structure

```
satquery-ai/
├── apps/{web, api}/
├── services/{agent, inference, geospatial, evidence, reporting}/
├── models/{vqa, detection, segmentation, change, corroboration}/
├── datasets/{manifests, preprocessing, evaluation}/
├── docs/
├── docker/
└── tests/
```

---

## 18. ₹0 Infrastructure Map

| Layer | Choice | Cost |
|---|---|---|
| Compute | Local RTX 4060 (dev + demo) | ₹0 |
| LLM | Ollama (local) + Gemini free tier (hybrid, rate-limited) | ₹0 within limits |
| Geospatial | GDAL/Rasterio/GeoPandas/PostGIS, local | ₹0 |
| Frontend hosting | Cloudflare Pages (static) | ₹0 within free tier |
| Source control | GitHub | ₹0 |
| GIS QA | QGIS | ₹0 |

Avoid: managed databases, paid GPU instances, paid LLM APIs, Mapbox paid tiers. If the demo itself runs off your laptop, you don't need hosting at all for judging day.

---

## 19. Development Timeline (assuming a ~36-hour onsite build — confirm your actual stage, see Open Questions)

| Phase | Hours | Deliverable |
|---|---|---|
| 0 | 0–3 | Repo, Docker, FastAPI/Next.js skeleton, Ollama running locally |
| 1 | 3–8 | Data pipeline: load AOI, display on map, metadata working |
| 2 | 8–16 | VQA (structured intents) + second single-image task working end-to-end |
| 3 | 16–24 | Change detection on a registered pair, quantified + rendered |
| 4 | 24–28 | SAR corroboration (P1 — cut first if behind schedule) |
| 5 | 28–32 | Agent routing across the above tools |
| 6 | 32–35 | Evidence panel + report export |
| 7 | 35–36 | Offline demo mode, rehearsal |

If this is actually the earlier idea/internal-round submission rather than the 36-hour grand finale, this timeline expands significantly and Phase 4 (SAR corroboration) and a real agent-trace UI become fully in-scope rather than stretch goals — worth re-running this table once you confirm the stage.

---

## 20. Judge Demo Flow (5 minutes)

1. Open with the AOI already loaded (don't burn demo time on file upload).
2. Ask: *"What changed here?"* → agent trace visibly runs → quantified answer + map overlay.
3. Click a region → evidence panel: before/after, mask, confidence breakdown.
4. Ask a corroboration question → show the honest "corroboration score," explicitly named as such.
5. Toggle offline mode live, repeat one query, to prove no internet dependency.
6. Export a report in one click.

## 21. Pitch Narrative (3 minutes)

Problem → the six-stage loop (*Ask → Plan → Analyze → Verify → Ground → Explain*) → why evidence-first design matters for a government/scientific user → what's honestly in scope vs. explicitly future work (Non-Goals, Section 4) → close on the offline-capable, ₹0 build as evidence of engineering discipline, not just ambition.

---

## 22. Open Questions (genuinely unresolved — resolve before deep-building)

| Question | Who/what resolves it | Blocking? |
|---|---|---|
| Exact wording of the official PS (background, dataset schema, grading rubric) | Official SIH PS PDF — paste it in for a precision pass on Section 5 | Yes |
| Does the ISRO/SAC dataset ship pre-registered optical/SAR pairs, or raw imagery requiring your own registration? | Same PDF / dataset documentation | Yes — changes Section 7.3/9 scope substantially |
| Which SIH stage is this PRD targeting — internal idea round or 36-hour grand finale? | You | Yes — changes Section 19 entirely |
| What GPU VRAM does the RTX 4060 variant actually have (6 GB vs 8 GB)? | `nvidia-smi` on your machine | No, but changes model-size choices in Section 7 |

---

*This PRD deliberately keeps Non-Goals and Open Questions as first-class sections — the biggest risk to a project this ambitious isn't insufficient ideas, it's insufficient scope discipline under a hard deadline.*
