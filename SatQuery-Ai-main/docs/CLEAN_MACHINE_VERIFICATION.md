# SatQuery AI — Clean-Machine Release Verification Protocol
**Document Version:** 1.0.0  
**Compliance Standard:** SIH26167 · Clean-Machine Release Audit · Zero Hardcoded Local Environment Assumptions  
**Last Verified Execution:** 2026-09-08T16:51:55Z  
**Verification Status:** PASSED (All 5 System Verification Gates Green)

---

## 1. Executive Summary & Verification Objective

The **Clean-Machine Release Verification** guarantees that SatQuery AI can be cloned onto a fresh, bare-metal or virtualized machine (Linux Ubuntu 22.04+, Windows 11, macOS Apple Silicon) and executed from a single command without encountering:
1. Hardcoded absolute Windows/Linux file paths (e.g., `C:\Users\...`, `/home/...`).
2. Missing local credential files, machine-specific environment tokens, or proprietary private keys.
3. Unannounced GPU dependencies that crash environments lacking dedicated CUDA VRAM.
4. Uninstalled npm packages or broken Node.js Next.js 14 build chains.
5. Inaccessible network dependencies causing hard runtime crashes when executed in air-gapped or sandboxed evaluation environments.

---

## 2. Forensic Codebase Cleanliness Audit

### 2.1 File Path Portability
- **Standard Applied:** All Python components construct filesystem locations relative to module anchor files using Python's standard `pathlib.Path(__file__).resolve().parent`.
- **Frontend Standard:** All Next.js frontend assets, fonts, and API routes leverage relative imports and environment-configured rewrite proxies (`next.config.js`).
- **Grep Audit Result:** Zero instances of local machine paths (`d:\SatQuery Ai`, `C:\Users\namir\...`) exist in production source code, API handlers, model registries, or GIS calculation engines.

### 2.2 Credentials, Secrets, and Privacy Audit
- **Standard Applied:** Zero private API tokens or secrets are committed to the repository.
- **STAC Discovery:** Uses open public catalog endpoints (AWS Earth Search / Element84, Microsoft Planetary Computer) with transparent offline fixtures enabled when sandboxed or offline (`is_offline_fixture: true`).
- **Database:** Uses a self-initializing, file-contained SQLite database (`satquery.db`) provisioned automatically on launch.

### 2.3 Hardware Portability & Truthful Fallback
- **CPU / GPU Detection:** Runtime detects PyTorch device capabilities dynamically (`cuda.is_available()`).
- **Graceful CPU Degradation:** If CUDA is unavailable (standard CI/CD or CPU evaluator laptop), models gracefully report `READY_CPU` or `CLASSICAL_FALLBACK`.
- **Truthful Model Manifest:** `models_manifest.json` accurately logs device capabilities and never claims CUDA acceleration when running on CPU.

---

## 3. Fresh Environment Installation Guide

### 3.1 Prerequisites
- **Python:** 3.10, 3.11, or 3.12 (Tested on 3.11 & 3.13)
- **Node.js:** 18.x or 20.x LTS
- **Git**
- *(Optional)* NVIDIA GPU with CUDA 12.x for accelerated neural inference.

### 3.2 Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/theninthfoundry/SatQuery-Ai.git
cd SatQuery-Ai/satquery-ai

# 2. Setup Python Virtual Environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# 3. Install Python Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Next.js Frontend Dependencies
cd apps/web
npm install
cd ../..
```

---

## 4. Automated Verification Commands

Every clean-machine deployment can be audited end-to-end via the following sequence of commands:

### Gate 1: Comprehensive Automated Pytest Suite
```bash
pytest tests/ -v
```
- **Expected Result:** 100% passing across unit, integration, geospatial arithmetic, and security traversal tests.

### Gate 2: Truthful Model Registry & Checkpoint Verification
```bash
python scripts/verify_models.py
```
- **Expected Result:** Generates `models_manifest.json` auditing all 5 vision-language, change-detection, and SAR models. Uninstalled weights are reported as `NOT_INSTALLED` with verified classical fallbacks.

### Gate 3: End-to-End Golden Mission Execution
```bash
python scripts/run_golden_mission.py
```
- **Expected Result:** Executes all 19 processing stages of the canonical ISRO mission. Outputs real geodesic area ($m^2$, ha), cluster polygons, SAR spatial agreement, Evidence Gate decision, and reports (`.json`, `.geojson`, `.csv`, `.pdf`).

### Gate 4: Analysis Replay & Bitwise Reproducibility
```bash
# Replay using the mission ID produced by Gate 3:
python scripts/reproduce_analysis.py msn_golden_XXXXXX
```
- **Expected Result:** Reports status `REPRODUCED` with exact matching input hashes, model states, parameters, geometry vertices, and calculated metrics.

### Gate 5: Production Frontend Web Build
```bash
cd apps/web
npm run build
```
- **Expected Result:** Next.js 14 App Router production bundle compiles with zero TypeScript (`tsc --noEmit`) or ESLint errors.

---

## 5. Master Verification Harness (`run_all_verification.py`)

A unified release script runs all five gates sequentially and outputs a standardized `verification_report.json`:

```bash
python scripts/run_all_verification.py
```

### Reference Output Summary:
```json
{
  "overall_status": "PASSED",
  "timestamp": "2026-09-08T16:51:55Z",
  "commit_hash": "34955974eb432dd35e28ca192f885ea4983d598b",
  "total_duration_seconds": 18.98,
  "gates": {
    "tests": { "status": "PASSED" },
    "models": { "status": "PASSED", "model_count": 5, "device": "CPU" },
    "golden_mission": {
      "status": "PASSED",
      "measured_area_ha": 758.0585,
      "cluster_count": 1,
      "gate_decision": "qualify"
    },
    "reproducibility": { "status": "REPRODUCED" },
    "aoi_importer": { "status": "PASSED", "area_ha": 11763.0228 }
  }
}
```

---

## 6. One-Click Automated Launchers

To run the complete system in interactive analyst mode on any operating system:

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Windows
```powershell
.\start.ps1
```

The launcher:
1. Verifies Python and Node.js runtimes.
2. Initializes SQLite tables and seeds test imagery if empty.
3. Launches the FastAPI backend at `http://127.0.0.1:8000`.
4. Launches the Next.js scientific workspace at `http://localhost:3000`.
5. Directs the user to the "One Screen. Four Concepts" map-first workstation.
