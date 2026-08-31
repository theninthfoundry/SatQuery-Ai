# SatQuery AI — Reproducibility & Evaluation Guide

**Problem Statement:** SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme  
**Target Environment:** Windows 10/11 or Ubuntu Linux · Single NVIDIA RTX 4060 GPU (8 GB VRAM) / CPU Fallback · Pure Python 3.10+ & Node.js 18+  

---

## 1. Quick Start (Single Reproducible Command)

### Windows
```powershell
.\start.ps1
```

### Linux / macOS
```bash
./start.sh
```

*The launcher automatically initializes the SQLite database, provisions upload/preview directories, seeds canonical ISRO demonstration datasets (Bangalore Urban Expansion, Brahmaputra Flood Dynamics, Sundarbans Mangrove Delta, Thar Canal), and starts both the FastAPI backend on port 8000 and Next.js Web Console on port 3000.*

---

## 2. Manual Step-by-Step Setup

### Step A: Clone & Python Environment
```bash
git clone <repository_url> satquery-ai
cd satquery-ai

python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step B: Frontend Environment
```bash
cd apps/web
npm install
npm run build
cd ../..
```

### Step C: Seed Demonstration Scenarios
```bash
python scripts/seed_demo_data.py
```

### Step D: Optional Neural Model Weight Activation
```bash
# Downloads 4-bit NF4 quantized GeoChat-7B weights (~4.5 GB) from Hugging Face
python scripts/download_geochat.py

# Optional: Train Siamese ChangeNet on synthetic paired satellite scenes
python scripts/train_changenet_synthetic.py
```

---

## 3. Running the Automated Test Suite

```bash
# Run unit, integration, and robustness test suite
pytest tests/ -v

# Run real model hardware gate
python scripts/verify_real_models.py
```

---

## 4. Evaluating the 5 Canonical Missions

Open the Web Console at `http://localhost:3000` and test the following inputs:

| Mission | Scenario | Query | Expected Result |
|---|---|---|---|
| **Mission 01 (VQA)** | Bangalore Urban Expansion | *"Describe the dominant land cover and major objects visible in this image."* | Land cover breakdown, multi-band statistics, and verified evidence card. |
| **Mission 02 (Grounding)** | Brahmaputra Flood Dynamics | *"Where is the largest water body?"* | Bounding box polygon mapped to central map with physical ground area in $m^2$. |
| **Mission 03 (Temporal)** | Bangalore Urban Expansion | *"What changed between these two observations and where?"* | Detected change regions (`01`, `02`), altered area ($2.56\text{ ha}$ / $25,600\text{ m}^2$), and swipe comparison slider. |
| **Mission 04 (Optical + SAR)** | Brahmaputra Flood Dynamics | *"Use both images together to identify regions that are likely built-up."* | SAR $\sigma^0$ radar backscatter analysis ($-14.5\text{ dB}$) with cross-modal concordance score. |
| **Mission 05 (Compound)** | Bangalore Urban Expansion | *"Has the built-up area increased between the two dates? Use the optical and SAR observations to corroborate the result and report the total changed area in hectares."* | Dual-pipeline execution (ChangeNet + DOFA), total altered area ($2.56\text{ ha}$), radar corroboration, and PDF/GeoJSON/CSV download buttons. |

---

## 5. Export Inspection

For any completed analysis, exports are downloadable via:
- **PDF Mission Dossier**: `http://localhost:8000/api/v1/reports/{job_id}/pdf`
- **RFC 7946 GeoJSON**: `http://localhost:8000/api/v1/reports/{job_id}/geojson`
- **CSV Tabular Metrics**: `http://localhost:8000/api/v1/reports/{job_id}/csv`
