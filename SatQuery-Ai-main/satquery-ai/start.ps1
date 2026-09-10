# SatQuery AI - Launcher Redirector
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootLauncher = (Resolve-Path (Join-Path $scriptDir "..\start.ps1")).Path
if (Test-Path $rootLauncher) {
    & $rootLauncher
} else {
    Write-Host "Launcher not found at $rootLauncher" -ForegroundColor Red
}
