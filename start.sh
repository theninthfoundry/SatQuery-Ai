#!/usr/bin/env bash
# SatQuery AI — One-Click Standalone Launcher (Linux / macOS)

set -e

echo "=========================================================================="
echo "                🛰️   SATQUERY AI — ONE-CLICK LAUNCHER                     "
echo "=========================================================================="

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo "🔄 Activating virtual environment..."
    source .venv/bin/activate
fi

# Pre-seed demonstration datasets
echo "📁 Pre-seeding demonstration datasets..."
python3 satquery-ai/scripts/seed_demo_data.py

# Ensure frontend dependencies are installed
if [ ! -d "satquery-ai/apps/web/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    (cd satquery-ai/apps/web && npm install)
fi

# Launch FastAPI Backend
echo "🚀 Launching FastAPI Backend on http://127.0.0.1:8000..."
cd satquery-ai
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Launch Next.js Web Console
echo "🖥️  Launching Next.js Mission Workspace on http://localhost:3000..."
cd satquery-ai/apps/web
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
