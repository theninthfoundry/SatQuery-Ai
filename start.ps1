# SatQuery AI - One-Click Standalone Launcher (Windows PowerShell)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $scriptDir "satquery-ai")) {
    $rootDir = $scriptDir
} elseif (Test-Path (Join-Path $scriptDir "..\..\satquery-ai")) {
    $rootDir = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
} elseif (Test-Path (Join-Path $scriptDir "..\satquery-ai")) {
    $rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path
} else {
    $rootDir = $scriptDir
}

Set-Location $rootDir

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "                SATQUERY AI - ONE-CLICK LAUNCHER                          " -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "Working root: $rootDir" -ForegroundColor DarkGray

# 1. Activate virtual environment if present
$venvScript = Join-Path $rootDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $venvScript
}

# 2. Pre-seed demo datasets
Write-Host "`nChecking demonstration datasets..." -ForegroundColor Yellow
$seedScript = Join-Path $rootDir "satquery-ai\scripts\seed_demo_data.py"
python $seedScript

# 3. Check and install frontend dependencies if needed
$webDir = Join-Path $rootDir "satquery-ai\apps\web"
$nodeModulesDir = Join-Path $webDir "node_modules"
if (!(Test-Path $nodeModulesDir)) {
    Write-Host "`nInstalling frontend dependencies in $webDir..." -ForegroundColor Yellow
    Push-Location $webDir
    npm install
    Pop-Location
}

# 4. Launch FastAPI Backend in background
Write-Host "`nLaunching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$appDir = Join-Path $rootDir "satquery-ai"
$backendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "backend.main:app", "--app-dir", "$appDir", "--host", "127.0.0.1", "--port", "8000" -PassThru

# 5. Launch Next.js Web Console
Write-Host "`nLaunching Next.js Mission Workspace on http://localhost:3000..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Push-Location $webDir
npm run dev

# Cleanup on exit
Pop-Location
Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
