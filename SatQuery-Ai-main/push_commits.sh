#!/usr/bin/env bash
set -e

echo "=== SatQuery AI: Staging and Pushing 6 Commits ==="

# Commit 1: GeoChat Multimodal Fix & Hardcoded Box Purge
echo -e "\n[1/6] Committing GeoChat Truthful Multimodal Adapter & Core Purge..."
git add satquery-ai/backend/models/geochat/adapter.py
git add satquery-ai/tests/unit/test_geochat_no_fallback_boxes.py
git add satquery-ai/backend/evidence/contract.py
git add satquery-ai/backend/models_db.py
git add satquery-ai/backend/reports/generator.py
git add satquery-ai/backend/assets/descriptor.py
git add satquery-ai/backend/geospatial/registration.py
git add satquery-ai/backend/api/routes/__init__.py
git add satquery-ai/apps/web/next.config.js
git commit -m "fix(geochat): purge hardcoded fallback boxes, add real multimodal tensor feeding, enforce transparent offline qualification"

# Commit 2: Spatial Ranking Engine, Water Body Analyzer, Invariant & Ambiguity Handling
echo -e "\n[2/6] Committing Deterministic Spatial Ranking, Water Body Analyzer & Invariants..."
git add satquery-ai/backend/agent/query_planner.py
git add satquery-ai/backend/geospatial/cloud.py
git add satquery-ai/backend/geospatial/water_body.py
git add satquery-ai/backend/engines/spatial_ranking.py
git add satquery-ai/backend/mission/parser.py
git add satquery-ai/backend/mission/planner.py
git add satquery-ai/backend/mission/executor.py
git add satquery-ai/backend/api/routes/analysis.py
git add satquery-ai/backend/agent/orchestrator.py
git add satquery-ai/tests/unit/test_water_body_analyzer.py
git add satquery-ai/tests/unit/test_cloud_quality_estimator.py
git add satquery-ai/tests/unit/test_water_body_ambiguity.py
git add satquery-ai/tests/unit/test_source_image_invariant.py
git add satquery-ai/tests/integration/test_spatial_ranking_pipeline.py
git commit -m "feat(spatial-ranking): implement deterministic water body analyzer, source-image invariant, and ambiguity qualification"

# Commit 3: Training Layer & Model Registry Provenance Taxonomy
echo -e "\n[3/6] Committing Training & Evaluation Layer with Model Registry Provenance..."
git add satquery-ai/training/
git add satquery-ai/backend/models/change/train_levir.py
git add satquery-ai/backend/models/change/infer.py
git add satquery-ai/backend/models/registry.py
git add satquery-ai/backend/api/routes/models.py
git add satquery-ai/scripts/verify_models.py
git add satquery-ai/models_manifest.json
git add models_manifest.json
git add satquery-ai/tests/unit/test_model_provenance_registry.py
git commit -m "feat(training): add training and evaluation layer with LEVIR-CD, VRSBench, and auditable model provenance taxonomy"

# Commit 4: Deterministic GIS, STAC, & Golden Mission Pipeline
echo -e "\n[4/6] Committing Golden Mission Pipeline & Analysis Replay Engine..."
git add satquery-ai/backend/geospatial/aoi_importer.py
git add satquery-ai/backend/api/routes/aoi.py
git add satquery-ai/backend/api/routes/images.py
git add satquery-ai/backend/ingestion/stac_client.py
git add satquery-ai/backend/api/routes/stac.py
git add satquery-ai/tests/unit/test_raster_metadata.py
git add satquery-ai/tests/integration/test_image_inspection_endpoint.py
git add satquery-ai/backend/pipelines/golden_mission.py
git add satquery-ai/scripts/run_golden_mission.py
git add satquery-ai/scripts/reproduce_analysis.py
git add satquery-ai/scripts/seed_demo_data.py
git add satquery-ai/tests/fixtures/synthetic_raster.py
git commit -m "feat(pipeline): complete 19-stage Golden Mission with SAR corroboration and bitwise analysis replay"

# Commit 5: Scientific Workstation UI & Genuine Polygon Map Rendering
echo -e "\n[5/6] Committing Scientific Workstation UI & Genuine GeoJSON Rendering..."
git add satquery-ai/apps/web/src/
git add satquery-ai/apps/web/package.json
git add satquery-ai/apps/web/package-lock.json
git commit -m "feat(ui): render authentic GeoJSON contour polygons and truthful calibration in scientific workstation"

# Commit 6: Master Release Verification, System Status & Auditable Documentation
echo -e "\n[6/6] Committing Master Verification Report & Documentation..."
git add satquery-ai/scripts/run_all_verification.py
git add satquery-ai/verification_report.json
git add verification_report.json
git add satquery-ai/SYSTEM_STATUS.yaml
git add SYSTEM_STATUS.yaml
git add satquery-ai/docs/
git add docs/
git add satquery-ai/README.md
git add README.md
git add push_commits.ps1
git add push_commits.sh
git commit -m "docs(architecture): update system status, release dossier, and SIH26167 architectural compliance report"

# Final clean staging for any remaining untracked helper files
git add -A
git status

echo -e "\n=== Pushing to GitHub Remote ==="
git push origin main || git push origin master

echo -e "\n=== All 6 Commits Pushed Successfully! ==="
