# SatQuery AI — Official SIH 2:30 Live Demonstration Script

**Scenario:** Bangalore Urban Expansion & Peripheral Infrastructure Corroboration  
**Total Duration:** 2 minutes 30 seconds  
**Primary Query (Mission 05):**  
> *"Has the built-up area increased between the two dates? Use the optical and SAR observations to corroborate the result and report the total changed area in hectares."*

---

## Live Demonstration Timeline

### `0:00 – 0:30` | The Problem & Vision
- **Speaker:**  
  *"Respected Evaluators, Earth observation satellites capture terabytes of imagery daily, but extracting actionable answers requires manual GIS toolchains, radar physics expertise, and complex software. SatQuery AI changes this paradigm: it turns natural language into structured, multi-sensor remote sensing computation."*
- **Action on Screen:**  
  Launch `http://localhost:3000`. The scientific workspace opens with the Bangalore Urban Expansion scenario loaded in the 60–65% satellite canvas.

---

### `0:30 – 0:45` | Natural-Language Dispatch
- **Speaker:**  
  *"Instead of asking a generic chatbot, we submit a compound scientific query: 'Has the built-up area increased between the two dates? Use optical and SAR to corroborate and report the changed area in hectares.'"*
- **Action on Screen:**  
  Click the suggested query chip or type into the bottom command bar and press Enter.

---

### `0:45 – 1:00` | 3-Layer Agent Orchestration & Execution Trace
- **Speaker:**  
  *"Notice our Agentic Router in action. It parses the intent as a Compound Multi-Modal Query. It validates that both multi-temporal pairs and SAR assets exist, then dispatches our Siamese ChangeNet CNN and DOFA Optical-SAR specialist sequentially."*
- **Action on Screen:**  
  The multi-step Agent Execution animation displays live steps:
  `01 Interpreting query` $\to$ `02 Validating spatial assets` $\to$ `03 Siamese ChangeNet` $\to$ `04 Affine polygonization` $\to$ `05 SAR corroboration` $\to$ `06 Building evidence`.

---

### `1:00 – 1:20` | Interactive Map & Temporal Controls
- **Speaker:**  
  *"The neural network generates a 2D change probability tensor, which our morphological contour head converts into real-world geographic polygons. On the map, we see altered clusters 01 and 02 highlighted in translucent coral red. We can use the Temporal Slider to swipe between the 2024 and 2026 acquisitions."*
- **Action on Screen:**  
  Drag the `Swipe` slider on the central map, demonstrating before/after surface alteration.

---

### `1:20 – 1:45` | Quantified Ground Measurements
- **Speaker:**  
  *"SatQuery does not hallucinate numbers. It dynamically reprojects the polygon vertices from WGS84 into the local metric UTM Zone 43N CRS via PyProj. It measures exactly 25,600 m²—which translates to 2.56 hectares of confirmed built-up expansion."*
- **Action on Screen:**  
  Point to the `MetricBlock` in the intelligence panel showing `2.56 ha`, `25,600 m²`, and `Evidence Score 91%`.

---

### `1:45 – 2:05` | Cross-Modal Radar Corroboration & Evidence
- **Speaker:**  
  *"To eliminate optical false positives like cloud shadows, SatQuery cross-examines Sentinel-1 C-band SAR radar backscatter. The -14.5 dB backscatter confirms urban surface reflection, yielding a 91% cross-modal concordance score."*
- **Action on Screen:**  
  Click on the `WhyThisAnswer` evidence drawer to reveal the calculation provenance and supporting evidence breakdown bars.

---

### `2:05 – 2:20` | Multi-Format Mission Dossier Export
- **Speaker:**  
  *"With a single click, decision-makers can export an audit-ready PDF mission dossier, RFC 7946 GeoJSON vector polygons for QGIS/ArcGIS, or tabular CSV logs."*
- **Action on Screen:**  
  Click `PDF Dossier` in the export panel to open the formatted mission report.

---

### `2:20 – 2:30` | Strong Closing Statement
- **Speaker:**  
  *"SatQuery AI does not just answer a question about satellite imagery. It determines how that question should be computed—giving decision-makers grounded, verified, and auditable remote sensing intelligence. Thank you."*
