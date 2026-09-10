#!/usr/bin/env bash
# SatQuery AI - Truth Lock v3 Push Script
set -e

echo "=== SatQuery AI: Staging and Pushing SATQUERY TRUTH LOCK v3 ==="

# 1. Frontend synthetic scientific generator purge
git add satquery-ai/apps/web/src/lib/geospatial.ts

# 2. Optical-SAR authentic spatial overlap & honest abstention
git add satquery-ai/backend/pipelines/optical_sar.py
git add satquery-ai/backend/mission/executor.py

# 3. Geospatial measured reliability & zero-fabrication factors
git add satquery-ai/backend/geospatial/water_body.py
git add satquery-ai/backend/geospatial/target_analyzers.py
git add satquery-ai/backend/engines/spatial_ranking.py

# 4. Status generator & multi-tier SIH matrix
git add satquery-ai/scripts/generate_system_status.py
git add satquery-ai/docs/SIH_REQUIREMENT_MATRIX.md
git add docs/SIH_REQUIREMENT_MATRIX.md

# 5. Unit tests
git add satquery-ai/tests/unit/test_truth_lock_v3_provenance.py

# 6. Commit
git commit -m "feat(truth-lock-v3): purge synthetic frontend generators, authentic optical-sar overlap, honest abstention, measured reliability factors, and multi-tier SIH matrix" || true

# Stage any remaining files
git add -A
git status

echo "=== Pushing to GitHub Remote ==="
git push origin main || git push origin master

echo "=== Truth Lock v3 Pushed Successfully! ==="
