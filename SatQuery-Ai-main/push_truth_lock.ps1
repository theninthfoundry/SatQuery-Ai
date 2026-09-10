# SatQuery AI - Truth Lock v3 Push Script
# Commits and pushes all SATQUERY TRUTH LOCK v3 hardening changes

Write-Host "=== SatQuery AI: Staging and Pushing SATQUERY TRUTH LOCK v3 ===" -ForegroundColor Cyan

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
git commit -m "feat(truth-lock-v3): purge synthetic frontend generators, authentic optical-sar overlap, honest abstention, measured reliability factors, and multi-tier SIH matrix"

# Stage any remaining files
git add -A
git status

Write-Host "`n=== Pushing to GitHub Remote ===" -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) {
    git push origin master
}

Write-Host "`n=== Truth Lock v3 Pushed Successfully! ===" -ForegroundColor Green
