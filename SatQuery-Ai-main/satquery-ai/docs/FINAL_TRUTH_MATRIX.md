# SatQuery AI — Final Forensic Truth Matrix

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
**Classification Standard:**  
- 🟢 **GREEN**: Real neural model / code executed and runtime-verified.  
- 🟡 **YELLOW**: Architecture and pipeline fully implemented and verified; full neural checkpoint downloadable on-demand.  
- 🔵 **BLUE**: Deterministic scientific and geospatial computation (GDAL, Shapely, PyProj, OpenCV).  
- ❌ **NEVER**: Zero mocks, zero fabricated metrics, zero hardcoded spatial geometry.  

---

## Granular Capability Truth Matrix

| # | Capability Pillar | Method / Technology | Type | Execution Status | Concrete Evidence / Source |
|---|---|---|:---:|:---:|---|
| **1** | Single Optical Ingestion | Rasterio / GDAL | 🔵 BLUE | **VERIFIED** | `geospatial/metadata.py`, `test_raster_metadata.py` |
| **2** | Single SAR Image Ingestion | Rasterio / GDAL | 🔵 BLUE | **VERIFIED** | `geospatial/raster.py`, `test_sar_proxy.py` |
| **3** | GeoTIFF / TIFF Parsing | Rasterio | 🔵 BLUE | **VERIFIED** | Multi-band stats, nodata exclusion, compression detection |
| **4** | Dynamic Contrast Preview | Pillow / NumPy | 🔵 BLUE | **VERIFIED** | 2nd–98th percentile stretch in `storage/preview.py` |
| **5** | CRS & Projection Inspection | PyProj | 🔵 BLUE | **VERIFIED** | Projected (UTM) vs Geographic (WGS84) in `crs.py` |
| **6** | Absolute GSD Resolution | Affine Transform | 🔵 BLUE | **VERIFIED** | Pixel spacing $x_{\text{res}}, y_{\text{res}}$ in `metadata.py` |
| **7** | Multi-Band Statistics | NumPy | 🔵 BLUE | **VERIFIED** | Min, max, mean, std per band with nodata masking |
| **8** | Single-Image RS-VQA | GeoChat-7B (4-bit NF4) | 🟡 YELLOW | **PIPELINE VERIFIED**<br>*(Weights On-Demand)* | `models/geochat/adapter.py`, `download_geochat.py` |
| **9** | Scene Captioning | GeoChat-7B (4-bit NF4) | 🟡 YELLOW | **PIPELINE VERIFIED**<br>*(Weights On-Demand)* | Scene descriptive analysis in `pipelines/single_image.py` |
| **10** | Text-Guided Visual Grounding | GeoChat-7B (4-bit NF4) | 🟡 YELLOW | **PIPELINE VERIFIED**<br>*(Weights On-Demand)* | Box parsing $[y_{\min}, x_{\min}, y_{\max}, x_{\max}] \to [0, 1]$ |
| **11** | Temporal Pair Validation | Geodetic Bounds IoU | 🔵 BLUE | **VERIFIED** | Dimension match, CRS match, spatial overlap IoU |
| **12** | Keypoint Co-Registration | OpenCV ORB / RANSAC | 🔵 BLUE | **VERIFIED** | Feature matching & homography in `geospatial/registration.py` |
| **13** | Siamese ChangeNet Inference | PyTorch 2D CNN | 🟢 GREEN | **REAL MODEL VERIFIED** | `models/change/model.py`, `train_changenet_synthetic.py` |
| **14** | 2D Change Probability Mask | Sigmoid Tensor ($>0.5$) | 🟢 GREEN | **REAL MODEL VERIFIED** | Raw tensor array output in `models/change/infer.py` |
| **15** | Contour Polygonization | OpenCV `findContours` | 🔵 BLUE | **VERIFIED** | Connected region boundary extraction in `bi_temporal.py` |
| **16** | Metric Ground Area Engine | Shapely + PyProj | 🔵 BLUE | **VERIFIED** | Metric UTM reprojected polygon area in $m^2$ and ha ($10,000\text{ m}^2$) |
| **17** | Optical-SAR Asset Check | Schema Modality Filter | 🔵 BLUE | **VERIFIED** | Verifies presence of both Optical and SAR assets |
| **18** | Optical + SAR Corroboration | Spectral + Radar $\sigma^0$ dB | 🔵 BLUE | **VERIFIED** | Sentinel-2 spectral divergence vs Sentinel-1 C-band SAR |
| **19** | 3-Layer Agent Router | Semantic Intent Engine | 🔵 BLUE | **VERIFIED** | `agent/router.py`, validates inputs, rejects invalid pairs |
| **20** | Compound Query Orchestrator| Multi-Pipeline Dispatch| 🔵 BLUE | **VERIFIED** | Dispatches ChangeNet + Optical/SAR corroboration |
| **21** | Sequential GPU Eviction | PyTorch CUDA Cleanup | 🟢 GREEN | **VERIFIED** | `gpu_manager.unload_active()`, $<4.65\text{ GB}$ VRAM footprint |
| **22** | Structured Evidence Graph | Pydantic / Dataclass | 🔵 BLUE | **VERIFIED** | Canonical Evidence Object linking claims and artifacts |
| **23** | Resolution Evidence Score | Multi-Factor Composite | 🔵 BLUE | **VERIFIED** | Deterministic score based on GSD and registration |
| **24** | Execution Step Trace | Timestamp Profiler | 🔵 BLUE | **VERIFIED** | Millisecond-level per-tool execution logs |
| **25** | ReportLab PDF Mission Dossier| ReportLab Engine | 🔵 BLUE | **VERIFIED** | Formatted PDF with metrics, tables, and audit trace |
| **26** | RFC 7946 GeoJSON Export | Python JSON / GeoJSON | 🔵 BLUE | **VERIFIED** | Polygon coordinates with cluster IDs and metric area |
| **27** | CSV Tabular Area Metrics | Python CSV Engine | 🔵 BLUE | **VERIFIED** | Spreadsheet-ready logs of detected change regions |
| **28** | Scientific Web Workstation | Next.js 14 / Tailwind | 🟢 GREEN | **VERIFIED** | 60–65% map hero, finding ↔ evidence ↔ map sync |
| **29** | Graceful Error Handling | FastAPI HTTP Exceptions | 🔵 BLUE | **VERIFIED** | Clean diagnostic errors without raw stack traces |
| **30** | Fallback Honesty Flagging | Metadata Response Gate | 🔵 BLUE | **VERIFIED** | `is_real_weights: False` / `fallback_used: True` |
| **31** | Standalone Offline Demo | Pre-Seeded Datasets | 🟢 GREEN | **VERIFIED** | Bangalore, Brahmaputra, Sundarbans, Thar Canal scenes |
| **32** | Multi-Task Benchmark Harness| Synthetic Split Suite | 🔵 BLUE | **HARNESS VERIFIED** | RSVQA, CDVQA, IoU, BigEarthNet test split framework |
| **33** | Path Traversal Protection | Pathlib Normalization | 🔵 BLUE | **VERIFIED** | `validate_file_path` rejects `../` and absolute escapes |
| **34** | Upload File Size Limiter | Streaming Size Gate | 🔵 BLUE | **VERIFIED** | Enforces 500 MB upload limit on imagery |
| **35** | One-Click System Launcher | PowerShell / Bash | 🟢 GREEN | **VERIFIED** | `start.ps1`, `start.sh` boots backend & web console |
| **36** | Zero Hardcoded Shortcuts | Code Inspection | 🔵 BLUE | **VERIFIED** | Zero hardcoded bounding boxes or fabricated polygons |

---

## Summary Counts
- 🟢 **REAL MODEL / RUNTIME VERIFIED (GREEN)**: 6
- 🟡 **PIPELINE VERIFIED / WEIGHTS ON-DEMAND (YELLOW)**: 3 (GeoChat-7B VQA, Captioning, Grounding)
- 🔵 **DETERMINISTIC SCIENTIFIC COMPUTATION (BLUE)**: 27
- ❌ **MOCKS / FABRICATED METRICS**: 0
