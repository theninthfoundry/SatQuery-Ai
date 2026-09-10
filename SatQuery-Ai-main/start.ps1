# SatQuery AI - Robust One-Click Launcher (Windows PowerShell)

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

# 1. Detect Python Executable (Prefer local .venv)
$venvPython = Join-Path $rootDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "Using virtual environment Python: $pythonExe" -ForegroundColor Yellow
} else {
    $pythonExe = "python"
    Write-Host "Using system Python" -ForegroundColor Yellow
}

# 2. Pre-seed demo datasets
Write-Host "`nChecking demonstration datasets..." -ForegroundColor Yellow
$seedScript = Join-Path $rootDir "satquery-ai\scripts\seed_demo_data.py"
& $pythonExe $seedScript

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
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", "backend.main:app", "--app-dir", "`"$appDir`"", "--host", "127.0.0.1", "--port", "8000" -PassThru

# Wait 2 seconds and test health
Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($health) {
        Write-Host "✓ Backend Health Check: OK (Status: $($health.status))" -ForegroundColor Green
    }
} catch {
    Write-Host "! Backend warming up..." -ForegroundColor DarkGray
}

# 5. Launch Next.js Web Console
Write-Host "`nLaunching Next.js Mission Workspace on http://localhost:3000..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Push-Location $webDir
try {
    npm run dev
} finally {
    Pop-Location
    if ($backendProcess -and !$backendProcess.HasExited) {
        Write-Host "`nStopping backend process..." -ForegroundColor DarkGray
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
