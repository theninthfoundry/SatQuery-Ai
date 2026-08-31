# SatQuery AI — Judge Mode & Live Evaluation Protocol

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
**Purpose:** An instant, zero-friction, evaluator-proof live demonstration protocol for SIH judges.  

---

## 1. Activating Judge Mode

In the SatQuery Web Console (`http://localhost:3000`), click the **`★ JUDGE MODE`** button in the top navigation bar or select any mission from the **Mission Selector Dropdown**.

When activated, the interface automatically loads:
1. The appropriate multi-sensor satellite imagery ($T_1$ Before, $T_2$ After, or Optical + SAR pair).
2. The exact natural-language scientific query.
3. Live geodetic metadata and CRS bounds.

---

## 2. The 5 Canonical Judge Missions

### Mission 05 ★ — Compound Multimodal Analysis (The Grand Showcase)
- **Scenario:** Bangalore Urban Expansion & Peripheral Infrastructure Corroboration
- **Input Sensors:** Sentinel-2 Optical (10m GSD) + Sentinel-1 SAR C-band
- **Evaluator Query:**
  > *"Has the built-up area increased between the two dates? Use the optical and SAR observations to corroborate the result and report the total changed area in hectares."*
- **What SatQuery Demonstrates:**
  1. **Agent Orchestration**: Recognizes compound intent and schedules both the Siamese ChangeNet CNN and DOFA Optical-SAR specialist.
  2. **Neural Change Map**: Dual-branch CNN generates a 2D probability tensor; topological contour polygonizer extracts Altered Clusters `01` and `02`.
  3. **Geospatial Area Engine**: Vertices are reprojected from WGS84 into local metric UTM Zone 43N CRS (`EPSG:32643`) to calculate **$25,600\text{ m}^2$ ($2.56\text{ ha}$)**.
  4. **SAR Radar Corroboration**: Cross-examines $-14.5\text{ dB}$ C-band backscatter to verify urban surface reflection and rule out optical cloud artifacts ($91\%$ concordance).
  5. **1-Click Export**: Generates audit-ready PDF mission dossier, RFC 7946 GeoJSON, and CSV metrics.

---

### Mission 01 — Single-Image RS-VQA
- **Scenario:** Bangalore Land Cover & Object Distribution
- **Input Sensors:** Sentinel-2 MSI (10m GSD)
- **Evaluator Query:**
  > *"Describe the dominant land cover and major objects visible in this image."*
- **What SatQuery Demonstrates:** Multi-spectral terrain parsing, 4-band statistics calculation, and descriptive land cover analysis linked to an auditable Evidence Card.

---

### Mission 02 — Text-Guided Visual Grounding & Metric Area
- **Scenario:** Brahmaputra Flood Dynamics & Inundated Water Basin
- **Input Sensors:** Sentinel-2 Multi-Spectral (10m GSD)
- **Evaluator Query:**
  > *"Where is the largest water body?"*
- **What SatQuery Demonstrates:** Neural bounding box coordinates $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$ mapped through the 6-element affine geotransform into real-world geographic coordinates with exact metric polygon area in $m^2$.

---

### Mission 03 — Bi-Temporal Surface Change Detection
- **Scenario:** Bangalore Peri-Urban Construction Corridors
- **Input Sensors:** Sentinel-2 Paired Observations (2024 vs 2026)
- **Evaluator Query:**
  > *"What changed between these two observations and where?"*
- **What SatQuery Demonstrates:** ORB/RANSAC keypoint co-registration, Siamese ChangeNet 2D probability map, translucent coral red cluster overlays on the map, and interactive Before/After Swipe Slider.

---

### Mission 04 — Optical + SAR Radar Corroboration
- **Scenario:** Brahmaputra Basin Cloud Penetration
- **Input Sensors:** Sentinel-2 Optical RGB + Sentinel-1 SAR C-band (VV/VH)
- **Evaluator Query:**
  > *"Use both images together to identify regions that are likely built-up."*
- **What SatQuery Demonstrates:** Optical spectral divergence cross-examined against SAR radar backscatter intensity ($-14.5\text{ dB}$) to establish quantitative cross-modal decision concordance.

---

## 3. Interactive Evidence Replay Feature

Under the **`WHY THIS ANSWER?`** panel, clicking **`View Execution Chain`** reveals the live, timestamped computational provenance trace:

```
00:00.12  INPUT ASSETS VALIDATED        (Optical T1/T2 + SAR C-band rasters verified on disk)
00:00.35  ORB / RANSAC CO-REGISTRATION  (Keypoint alignment verified, IoU: 95%)
00:00.58  SIAMESE CHANGENET INFERENCE   (2D Sigmoid Probability Tensor generated, >0.5 threshold)
00:00.72  CONTOUR POLYGONIZATION        (OpenCV topological boundary tracing: 2 distinct clusters)
00:00.86  OPTICAL SPECTRAL ANALYSIS     (RGB / NDWI spectral reflectance divergence calculated)
00:00.99  SAR RADAR CORROBORATION       (-14.5 dB σ⁰ backscatter confirms urban surface change)
00:01.15  GEOSPATIAL AREA ENGINE        (WGS84 → UTM Zone 43N metric area: 25,600 m² / 2.56 ha)
00:01.28  EVIDENCE & PROVENANCE GRAPH   (Multi-factor Evidence Score: 91%)
```
