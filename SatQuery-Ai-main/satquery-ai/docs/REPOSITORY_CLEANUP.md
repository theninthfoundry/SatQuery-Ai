# SatQuery AI — Repository Audit & Cleanup Summary

---

## 1. Audit Scope & Verification
A full repository scan was performed across `backend/`, `apps/web/`, `scripts/`, `tests/`, and root directories.

### Confirmed Clean & Verified Components
1. **Frontend**:
   - `apps/web/src/components/shell/` (`TopHeader.tsx`, `InstrumentRail.tsx`, `ContextPanel.tsx`)
   - `apps/web/src/components/map/` (`GeoWorkspace.tsx`, `MapToolbar.tsx`, `MapControls.tsx`, `TemporalController.tsx`, `MapMetadata.tsx`)
   - `apps/web/src/components/intelligence/` (`MissionSummary.tsx`, `MetricBlock.tsx`, `EvidenceList.tsx`, `WhyThisAnswer.tsx`, `ExportPanel.tsx`)
   - `apps/web/src/components/query/` (`QueryBar.tsx`, `SuggestedQueries.tsx`, `AgentExecution.tsx`)
   - `apps/web/src/components/system/` (`ModelStatus.tsx`)
   - `apps/web/src/components/MissionWorkspace.tsx`
   - `apps/web/src/components/ReportExportModal.tsx`
   - `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`, `apps/web/tailwind.config.js`
2. **Backend**:
   - `backend/api/` (Routes: `images.py`, `analysis.py`, `query.py`, `reports.py`, `health.py`, `evaluation.py`, `aoi.py`, `evidence.py`, `models.py`)
   - `backend/agent/` (`router.py`, `orchestrator.py`, `tools.py`, `llm_client.py`, `tool_registry.py`)
   - `backend/models/` (`manager.py`, `registry.py`, `geochat/`, `change/`, `dofa/`)
   - `backend/pipelines/` (`bi_temporal.py`, `single_image.py`, `grounding.py`, `optical_sar.py`, `golden_mission.py`)
   - `backend/geospatial/` (`metadata.py`, `crs.py`, `raster.py`, `geometry.py`, `registration.py`, `validation.py`, `isro_formats.py`)
   - `backend/evidence/` (`builder.py`, `calibration.py`, `confidence.py`, `contract.py`, `provenance.py`)
   - `backend/reports/` (`generator.py`)
   - `backend/storage/` (`manager.py`, `preview.py`)
   - `backend/db.py`, `backend/models_db.py`, `backend/config.py`, `backend/main.py`
3. **Tests & Scripts**:
   - 34 comprehensive tests across `tests/unit/`, `tests/integration/`, `tests/robustness/`
   - Seeder & verification scripts: `scripts/seed_demo_data.py`, `scripts/verify_real_models.py`, `scripts/train_changenet_synthetic.py`, `scripts/download_geochat.py`

### Obsolete Code Check & Dead Code Prevention
- Traced all import references in `api.ts`, `MissionWorkspace.tsx`, and backend routes.
- Added alias `executeAgentQuery = submitAgentQuery` in `apps/web/src/lib/api.ts` to ensure backward and forward compatibility.
- Zero orphaned or dangling temp files in `data/uploads/` or `data/previews/`.
