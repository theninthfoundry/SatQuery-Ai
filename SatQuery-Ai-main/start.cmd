@echo off
REM SatQuery AI - Double-Click / CMD Launcher
cd /d "d:\SatQuery Ai"

echo ==========================================================================
echo                 SATQUERY AI - ONE-CLICK LAUNCHER
echo ==========================================================================

REM 1. Choose Python
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo Using virtual environment Python
) else (
    set "PYTHON_EXE=python"
    echo Using system Python
)

REM 2. Seed data
echo.
echo Seeding demonstration datasets...
%PYTHON_EXE% satquery-ai\scripts\seed_demo_data.py

REM 3. Launch Backend in background
echo.
echo Launching FastAPI Backend on http://127.0.0.1:8000...
start /b "" %PYTHON_EXE% -m uvicorn backend.main:app --app-dir "satquery-ai" --host 127.0.0.1 --port 8000

REM 4. Open browser
timeout /t 2 >nul
start http://localhost:3000

REM 5. Launch Next.js
echo.
echo Launching Next.js Web Workspace on http://localhost:3000...
cd "satquery-ai\apps\web"
npm run dev
