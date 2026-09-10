# SatQuery AI — Developer Guide

This guide covers local environment setup, running the backend and frontend, running tests, and code formatting.

---

## 1. Prerequisites

- **Python**: 3.10, 3.11, or 3.12
- **Node.js**: 18.x or 20.x LTS + `npm`
- **Git**
- **NVIDIA GPU** (Optional for Phase 0; required for Phase 1 VLM inference)

---

## 2. Backend Setup

### Create Virtual Environment & Install Dependencies:

```bash
# From satquery-ai repository root
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Backend Server:

```bash
# Start FastAPI with hot reload on port 8000
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend health:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs` (Swagger UI)

---

## 3. Frontend Setup

### Install Dependencies & Start Next.js:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 4. Running the Test Suite

Run unit and integration tests using pytest:

```bash
# Run full test suite with verbose output
pytest -v

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v
```

---

## 5. Code Formatting & Linting

```bash
# Verify Python compilation across backend
python -m compileall backend

# Lint with Ruff
ruff check backend tests

# Type check
mypy backend
```
