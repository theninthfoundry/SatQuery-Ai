# SatQuery AI — Canonical Architecture

**Version**: 1.0  
**Status**: AUTHORITATIVE  
**Last Updated**: 2026-09-09

## Non-Negotiable Principle

> THE LLM/VLM IS NEVER THE SCIENTIFIC SOURCE OF TRUTH.
>
> All geometry, coordinates, area, distance, CRS, spectral measurements, sensor agreement metrics,
> change percentages, benchmark scores, confidence values, and provenance originate from:
> actual raster/image observations, deterministic calculations, actual model outputs,
> recorded runtime metadata, evidence contracts, and validated benchmark results.

## Single Authoritative Execution Path

```
USER QUERY
    ↓
MISSION / QUERY PLANNER          ← backend/mission/parser.py, backend/agent/query_planner.py
    ↓
INPUT + OBSERVATION VALIDATION   ← backend/assets/, backend/geospatial/validation.py
    ↓
CAPABILITY ROUTER                ← backend/agent/router.py, backend/agent/orchestrator.py
    ↓
SPECIALIST MODEL(S)              ← backend/models/{geochat,change,dofa,sam}/adapter.py
  + DETERMINISTIC GIS ENGINE(S)  ← backend/geospatial/, backend/engines/
    ↓
EVIDENCE BUILDER                 ← backend/evidence/builder.py, contract.py
    ↓
EVIDENCE GRAPH                   ← backend/evidence/graph.py
    ↓
EVIDENCE GATE                    ← backend/evidence/gate.py
    ↓
CANONICAL ANALYSIS RESULT        ← backend/evidence/contract.py (EvidenceContract)
    ↓
MAP / INTELLIGENCE PANEL         ← apps/web/src/components/
  / REPORT / REPLAY              ← backend/reports/generator.py
```

## Authoritative Source Trees

| Component | Path | Status |
|---|---|---|
| Backend API | `satquery-ai/backend/` | AUTHORITATIVE |
| Frontend App | `satquery-ai/apps/web/` | AUTHORITATIVE |
| Tests | `satquery-ai/tests/` | AUTHORITATIVE |
| Scripts | `satquery-ai/scripts/` | AUTHORITATIVE |
| Training | `satquery-ai/training/` | REFERENCE |
| Archive | `_archive/` | DEPRECATED (reference only) |

## There is NO second production backend.

The previous `satquery-complete/` tree has been moved to `_archive/satquery-complete-reference/`.
No production code may import from `_archive/`.

## Model Registry Authority

All models and deterministic engines are registered in:
- `backend/models/registry.py` — Python registry singleton
- `backend/models/registry.yaml` — Static metadata

A model is READY only when ALL of:
1. Checkpoint exists
2. Checkpoint integrity verified
3. Architecture compatible
4. Weights load successfully
5. Model inference executes successfully
6. Input tensor contract passes
7. Output schema passes
8. Actual input changes can affect output
9. Runtime device is recorded
10. VRAM/memory requirement passes
11. No silent fallback occurred

## Evidence Gate Authority

Every analysis route MUST end through `EvidenceGate.evaluate()`.

Possible decisions:
- **ANSWER**: Sufficient, high-quality corroborating evidence
- **QUALIFY**: Answer provided with mandatory scientific caveats
- **ABSTAIN**: Explicit scientific refusal when evidence is invalid

No pipeline may return a result without gate evaluation.

## Fallback Semantics

When a neural model is unavailable:
- `execution_mode` must state `CLASSICAL_FALLBACK` or `OFFLINE_FALLBACK`
- `model` must be `null` or identify the fallback engine
- `is_real_weights` must be `false`
- `truth_state` must be `FALLBACK` or `UNTRAINED_MODEL`

A classical/deterministic technique MUST NOT inherit neural-model provenance labels.
