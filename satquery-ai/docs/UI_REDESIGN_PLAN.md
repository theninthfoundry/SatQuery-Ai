# SatQuery AI — UI Redesign & Premium Product Architecture Plan

## 1. Overview & Architectural Vision
SatQuery AI is being transformed from a dense, dark mission-control developer dashboard into a **refined, mostly-white, black-and-white scientific intelligence interface**. It embodies:
- **Apple-level restraint & clarity**: Generous whitespace, clean typography, intentional hierarchy.
- **Linear-level craft & micro-interactions**: Subtly elevated active states, seamless tooltips, responsive inputs.
- **Palantir-level analytical rigor**: Grounded spatial calculations, audited evidence layers, zero hallucination.
- **Modern Earth-Observation Instrument**: The satellite imagery occupies 60–65% of the central canvas and is the visual hero.

---

## 2. Design System & Tokens

### Color Palette
- **Primary Canvas**: `#FFFFFF` / `#F8F8F6` / `#F3F3F0` (light warm gray)
- **Primary Text**: `#111111` / `#171717` (deep carbon)
- **Secondary Text**: `#666666` / `#888888` (neutral gray)
- **Borders & Dividers**: `#E8E8E5` / `#EDEDE9` (ultra-subtle warm gray)
- **Instrument Rail & High-Contrast Elements**: `#0A0A0A` (deep obsidian black)
- **Semantic Accents**:
  - **Success / Valid / Calibrated**: Restrained Emerald `#10B981` / `#059669`
  - **Change / Detection Regions**: Restrained Red / Coral `#EF4444` / `rgba(239, 68, 68, 0.22)`
  - **SAR / Optical Corroboration**: Restrained Cyan `#0EA5E9` / `#0284C7`
  - **Warning**: Warm Amber `#F59E0B`

### Typography
- **Headings & Body**: `Inter`, `Geist Sans`, system-ui
- **Technical Telemetry & Numbers**: `Geist Mono`, `JetBrains Mono`, `ui-monospace` (GSD, CRS, UTM coordinates, areas, ECE calibration)

### Spacing & Elevation
- **Spacing Scale**: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 48px
- **Border Radii**: 8px (small badges/inputs), 12px (cards/viewport), 16px (panels/modals), 9999px (pills)
- **Shadows**: `0 1px 3px rgba(0,0,0,0.04)`, `0 4px 12px rgba(0,0,0,0.06)`

---

## 3. Component Hierarchy & Module Breakdown

```
src/
├── app/
│   ├── globals.css                # New light-mode design tokens & base utilities
│   ├── layout.tsx                 # Inter/Geist fonts & metadata
│   └── page.tsx                   # Top-level workspace & diagnostics router
├── components/
│   ├── shell/
│   │   ├── TopHeader.tsx          # SATQUERY AI brand, Mission pill selector, Tabs, GPU & user
│   │   ├── InstrumentRail.tsx     # Narrow black vertical rail (MISSION, DATA, LAYERS, ANALYSIS, EVIDENCE, TRACE, EXPORT, SETTINGS)
│   │   └── ContextPanel.tsx       # Left contextual panel (Scene Assets 01-05, Active Datasets cards)
│   ├── map/
│   │   ├── GeoWorkspace.tsx       # Dominant ~60-65% satellite map canvas
│   │   ├── MapToolbar.tsx         # VIEW: True Color, NIR, SAR, CHANGE, EVIDENCE & OVERLAYS
│   │   ├── MapControls.tsx        # Vertical floating tools: Select, Polygon, Box, Pin, Ruler, Zoom
│   │   ├── TemporalController.tsx # T1 / T2 date slider with Swipe, Side-by-Side, Difference modes
│   │   └── MapMetadata.tsx        # Scale bar, coordinates, EPSG:4326, 10m GSD
│   ├── intelligence/
│   │   ├── MissionSummary.tsx     # Status: Completed, Synthesized Insight
│   │   ├── MetricBlock.tsx        # ALTERED AREA (ha / m²), CALIBRATED ECE (Platt Logistic)
│   │   ├── EvidenceList.tsx       # Verified Evidence layers with interactive Map linking
│   │   ├── WhyThisAnswer.tsx      # Expandable scientific execution & consistency drawer
│   │   └── ExportPanel.tsx        # Direct 1-click export triggers (PDF, GeoJSON, CSV, KML)
│   ├── query/
│   │   ├── QueryBar.tsx           # Floating AI command input with voice/dispatch
│   │   ├── SuggestedQueries.tsx   # Domain-specific scenario prompts
│   │   └── AgentExecution.tsx     # Sequential 6-step agent execution state
│   ├── system/
│   │   ├── ModelStatus.tsx        # Bottom status bar (Models Ready, Integrity, Offline Mode)
│   │   └── DiagnosticsView.tsx    # Clean diagnostics & raw raster ingestion suite
│   └── MissionWorkspace.tsx       # Orchestrates full state, map synchronizations & queries
```

---

## 4. Key Interaction Models

### 1. Map ↔ Evidence Linking
- Clicking **Siamese ChangeNet** highlights change contours and toggles the probability mask.
- Clicking **Optical Reflectance** flips map visualization to true/spectral divergence.
- Clicking **Affine Geotransform Head** outlines polygon geometry and displays UTM coordinate projections.
- Clicking any **Cluster (01, 02)** on the map or panel zooms and focuses on the exact region with computed metric area ($m^2$, ha).

### 2. Multi-Step Agent Execution Animation
When a query is dispatched, the query bar transitions to an active execution trace:
1. `01 Interpreting query` [✓]
2. `02 Validating imagery & CRS` [✓]
3. `03 Selecting specialist neural head` [✓]
4. `04 Detecting surface change / grounding` [●]
5. `05 Computing geodesic metric area` [○]
6. `06 Building verified evidence & ECE` [○]

### 3. Temporal Slider & Compare Modes
- **Swipe Mode**: Interactive split slider between T1 (2024) and T2 (2026).
- **Side by Side**: Dual synchronized viewports.
- **Difference Mode**: Highlighting pixel difference vectors.

---

## 5. API & Backend Contract Alignment
The redesign maintains 100% compatibility with:
- `GET /api/v1/health` (GPU, torch, CUDA, hardware status)
- `GET /api/v1/images` (Ingested scene assets)
- `POST /api/v1/query` (Agent orchestration with real intent routing & execution trace)
- `POST /api/v1/analysis/change` (Bi-temporal ChangeNet execution)
- `POST /api/v1/analysis/grounding` (GeoChat grounding & bounding polygons)
- `POST /api/v1/analysis/optical-sar` (DOFA optical + SAR fusion)
- `GET /api/v1/reports/{job_id}/{format}` (Downloadable PDF, GeoJSON, and CSV mission dossiers)
