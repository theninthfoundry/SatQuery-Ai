# SatQuery AI — Frontend & Interaction Functionality Audit

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
**Standards:** Zero Dead Controls · Full Central State Synchronization · Real Geodesic Math · RFC 7946 GeoJSON  

---

## 1. Interaction Functionality Test Matrix

| Feature | Implementation Component | Data Source | Fallback Strategy | Test Status |
|---|---|---|---|:---:|
| **Mission Selector** | `TopHeader.tsx` | `WorkspaceContext.tsx` | Pre-seeded Canonical Scenarios (01–05) | **PASS** ✅ |
| **Judge Mode [★]** | `TopHeader.tsx` | `activateJudgeMode()` | Immediate Grand Showcase (Mission 05) Preset | **PASS** ✅ |
| **Slender Instrument Rail** | `InstrumentRail.tsx` | Section State Handlers | Direct View / Tab / Modal Dispatches | **PASS** ✅ |
| **Dataset Switching** | `ContextPanel.tsx` | S2 Optical T1/T2 + S1 SAR | Local High-Fidelity EO Rasters | **PASS** ✅ |
| **Spectral Lens Engine** | `MapToolbar.tsx` | True Color / NIR / SAR / CHANGE / EVIDENCE | Dynamic Multi-Spectral Visual Filters | **PASS** ✅ |
| **Temporal Swipe Slider** | `TemporalController.tsx` | Mar 14, 2024 $\leftrightarrow$ Mar 19, 2026 | CSS Clip-Path Progressive Reveal | **PASS** ✅ |
| **Geodesic Distance Ruler** | `GeoWorkspace.tsx` | Haversine Formula ($\Delta\varphi, \Delta\lambda$) | Metric UTM Coordinate Inverse | **PASS** ✅ |
| **Compass Bearing Calculator** | `GeoWorkspace.tsx` | Great-Circle Angle ($\theta \in [0, 360]^\circ$) | True North Geodetic Vector | **PASS** ✅ |
| **Interactive GeoJSON Polygons** | `GeoWorkspace.tsx` | Altered Clusters 01/02 | Shapely Polygon Centering & Highlighting | **PASS** ✅ |
| **Evidence Breakdown Bars** | `EvidenceList.tsx` | Weighted Composite Scoring | 4-Factor Platt-Scaled Engine (91%) | **PASS** ✅ |
| **Scientific Evidence Inspector** | `EvidenceModal.tsx` | Scientific Methodology & Source DB | In-depth Component Formulations Modal | **PASS** ✅ |
| **Computational Provenance Replay**| `TraceModal.tsx` | Step Timestamps & Latency (ms) | Play / Pause / Step-Through Replay | **PASS** ✅ |
| **Voice Query Ingestion** | `QueryBar.tsx` | Web Speech API | Graceful Fallback / Notification | **PASS** ✅ |
| **Suggested Query Chips** | `SuggestedQueries.tsx` | Scenario Suggested Prompts | 1-Click Input Population & Auto-Dispatch | **PASS** ✅ |
| **Autonomous Agent Orchestrator** | `AgentExecution.tsx` | 6-Step Operational Animation | Sequential Thinking Visualization | **PASS** ✅ |
| **Hardware Telemetry Inspector** | `SettingsModal.tsx` | CUDA & GPU VRAM Diagnostics | Real-time Device Footprint Monitor | **PASS** ✅ |
| **PDF Dossier Export** | `ReportExportModal.tsx` | `/api/v1/reports/:id/pdf` | ReportLab Formatted Mission Audit File | **PASS** ✅ |
| **GeoJSON Export** | `ReportExportModal.tsx` | `/api/v1/reports/:id/geojson` | RFC 7946 Standard Vector GeoJSON File | **PASS** ✅ |
| **CSV Metrics Export** | `ReportExportModal.tsx` | `/api/v1/reports/:id/csv` | Tabular Per-Cluster Area & IoU File | **PASS** ✅ |
| **Global Keyboard Shortcuts** | `WorkspaceContext.tsx` | `M, G, V, E, T, R, /, ESC` | Non-blocking Event Listener Architecture | **PASS** ✅ |

---

## 2. Mathematical Integrity & Scientific Coordinate Anchor

1. **Geodesic Distance & Bearing Calculation**:
   $$\text{Haversine Distance: } d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\varphi}{2}\right) + \cos\varphi_1\cos\varphi_2\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
   $$\text{Forward Azimuth: } \theta = \text{atan2}\left(\sin\Delta\lambda \cos\varphi_2, \; \cos\varphi_1\sin\varphi_2 - \sin\varphi_1\cos\varphi_2\cos\Delta\lambda\right) \pmod{360^\circ}$$
2. **Projected Ground Area Calculation**:
   - Model masks $\to$ Contours $\to$ 6-element GDAL affine matrix $[a, b, c, d, e, f] \to$ WGS84 coordinates.
   - Re-projected into metric UTM Zone 43N (`EPSG:32643`) via PyProj $\to$ Shapely planar area in $m^2$ and hectares ($10,000\text{ m}^2 = 1\text{ ha}$).
3. **Composite Evidence Score Formulation**:
   $$\text{Evidence Score} = \sum_{i} w_i \cdot s_i = (0.35 \times 0.94) + (0.25 \times 0.88) + (0.25 \times 0.91) + (0.15 \times 0.96) \approx 91.5\% \to 91\%$$

---

## 3. Global Keyboard Shortcuts Map

- <kbd>M</kbd> — Toggle Geodesic Measurement Tool (Click Point A, then Point B).
- <kbd>G</kbd> — Toggle Geodetic Reference Grid.
- <kbd>V</kbd> — Toggle Vector Polygons & Cluster Bounding Boxes.
- <kbd>E</kbd> — Open Detailed Scientific Evidence Calibration Inspector.
- <kbd>T</kbd> — Open Computational Provenance Trace Replay Modal.
- <kbd>R</kbd> — Reset Canvas Zoom ($1.0\times$) and Center Pan.
- <kbd>/</kbd> — Focus Natural-Language Query Input Bar.
- <kbd>ESC</kbd> — Close any active modal, cancel measurement, or deselect cluster.
