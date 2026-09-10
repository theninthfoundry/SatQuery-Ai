# SatQuery AI — SIH 2024 Evaluator Presentation & Pitch Deck

**Problem Statement:** SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme  
**Theme:** Natural Language to Multi-Sensor Geospatial Computation  

---

### Slide 1: Title & Vision
**SatQuery AI: Ask a Satellite Anything**
- *Subtitle*: An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Natural-Language Queries.
- *Tagline*: Grounded Remote Sensing Intelligence · Zero Fabrication · Full Geospatial Provenance.

---

### Slide 2: The Problem
**Earth Observation Data is Powerful but Inaccessible**
- Earth Observation satellites (ISRO Resourcesat, Cartosat, Sentinel-1/2) capture terabytes of multi-spectral and radar data daily.
- Interpreting this data requires specialized GIS toolchains, domain knowledge in radar physics, and manual analysis.
- Decision-makers need instant, natural-language answers backed by physical ground measurements.

---

### Slide 3: Our Core Insight
**Natural Language $\to$ Structured Computational Workflows**
- SatQuery does not treat satellite analysis as a pure text generation problem.
- Instead, natural-language queries are parsed into structured computational pipelines dispatching specialized vision-language models, deep convolutional networks, and deterministic geospatial mathematics.

---

### Slide 4: System Architecture
**Agentic Router $\to$ Heterogeneous Specialists $\to$ Evidence Engine $\to$ GIS**
- **Query Layer**: 3-layer semantic router with input asset validation and error rejection.
- **Specialist Heads**: GeoChat-7B (4-bit VLM), Siamese ChangeNet (PyTorch 2D CNN), DOFA (Spectral + SAR Corroboration).
- **Geospatial Head**: GDAL/Rasterio/PyProj metric projected UTM area computation.
- **Evidence Layer**: Canonical Evidence Objects with Platt-scaled Evidence Scores and millisecond-level execution traces.

---

### Slide 5: Single-Image Remote Sensing Intelligence
**RS-VQA & Text-Guided Visual Grounding**
- Natural-language inquiries (*"Where is the largest water body?"*) produce bounding box coordinates $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$.
- Bounding boxes are dynamically transformed via the raster's 6-element affine geotransform into real-world geographic coordinates with physical ground area ($m^2$, ha).

---

### Slide 6: Temporal Surface Intelligence
**Bi-Temporal Surface Change Detection**
- Ingests paired before/after rasters ($T_1, T_2$).
- Automated ORB/RANSAC keypoint co-registration check.
- Siamese ChangeNet dual-branch CNN generates 2D sigmoid probability maps.
- Morphological contour polygonization extracts distinct altered clusters with metric area.

---

### Slide 7: Cross-Modal Intelligence
**Optical Reflectance + SAR Radar Corroboration**
- Cloud cover and shadow artifacts deceive optical sensors; smooth surfaces deceive radar.
- SatQuery combines Sentinel-2 optical spectral indices with Sentinel-1 C-band SAR $\sigma^0$ radar backscatter ($-14.5\text{ dB}$) to establish quantitative cross-modal decision concordance.

---

### Slide 8: The Grand Showcase (Mission 05)
**Compound Multi-Modal Temporal Analysis**
- *Query*: *"Has the built-up area increased between the two dates? Use the optical and SAR observations to corroborate the result and report the total changed area in hectares."*
- Agent orchestrates ChangeNet + Optical Analysis + SAR Analysis $\to$ extracts $2.56\text{ ha}$ ($25,600\text{ m}^2$) alteration $\to$ confirms $-14.5\text{ dB}$ radar backscatter consistency ($91\%$ concordance) $\to$ exports PDF/GeoJSON/CSV dossiers.

---

### Slide 9: Scientific Evidence & Auditability
**Every Finding is Traceable and Verified**
- No black-box guesses.
- Each answer is coupled with:
  - Exact model name, version, and execution mode.
  - Multi-factor Evidence Score (Resolution GSD + Registration + Model Logits).
  - Downloadable ReportLab PDF, RFC 7946 GeoJSON, and CSV spreadsheets.

---

### Slide 10: Quantitative Evaluation & Benchmarking
**Multi-Task Validation on Standard Benchmarks**
- Comprehensive harness testing RSVQA-HR, VRSBench, CDVQA, and BigEarthNet splits.
- Zero fabricated metrics; transparent labeling between harness test runs and full benchmark suites.

---

### Slide 11: Hardware Feasibility & Zero-Budget Deployment
**High Performance within an 8 GB VRAM Envelope**
- Runs entirely on a single consumer NVIDIA RTX 4060 Laptop GPU (8 GB VRAM) or CPU fallback.
- Sequential GPU model manager evicts inactive models, keeping peak VRAM consumption below $4.65\text{ GB}$.
- 100% offline-capable with pre-seeded ISRO demonstration datasets.

---

### Slide 12: Why SatQuery AI?
**One Interface · Multiple Sensors · Multiple Models · One Auditable Answer**
- Bridges natural language and remote sensing science.
- Eliminates AI hallucination through geometric grounding.
- Ready for deployment across disaster management, urban planning, agriculture, and defense.
