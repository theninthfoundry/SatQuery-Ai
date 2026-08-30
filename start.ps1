# SatQuery AI — One-Click Standalone Launcher (Windows PowerShell)

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "                🛰️   SATQUERY AI — ONE-CLICK LAUNCHER                     " -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan

# 1. Activate virtual environment if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    & ".\.venv\Scripts\Activate.ps1"
}

# 2. Pre-seed demo datasets
Write-Host "`n📁 Checking demonstration datasets..." -ForegroundColor Yellow
python satquery-ai/scripts/seed_demo_data.py

# 3. Launch FastAPI Backend in background
Write-Host "`n🚀 Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "backend.main:app", "--app-dir", "satquery-ai", "--host", "0.0.0.0", "--port", "8000" -PassThru

# 4. Launch Next.js Web Console
Write-Host "`n🖥️  Launching Next.js Mission Workspace on http://localhost:3000..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Set-Location "satquery-ai/apps/web"
npm run dev

# Cleanup on exit
Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
