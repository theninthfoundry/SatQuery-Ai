# SatQuery AI — Evaluator FAQ & Technical Defense

**Smart India Hackathon 2024 · Problem Statement SIH26167 · Indian Space Research Organisation (ISRO)**  
**Target Audience:** SIH Judges, Remote Sensing Scientists, ISRO/SAC Evaluators, ML Engineers  

---

### Q1: Why use an agentic architecture instead of a single giant Vision-Language Model (VLM)?
**Answer:** Single monolithic VLMs are notorious for spatial hallucination, cannot compute metric polygon areas ($m^2$, ha), fail to ingest multi-temporal pairs with high-resolution pixel registration, and cannot natively process radar backscatter ($\sigma^0$ in dB). SatQuery AI uses an **Agentic Router** that treats natural language as a query intent, dispatching dedicated specialist perception heads (Siamese ChangeNet for temporal change, DOFA for optical/SAR, GeoChat for text grounding) and deterministic geospatial heads (GDAL/Shapely) to produce auditable, grounded answers.

---

### Q2: Why use multiple specialist models instead of fine-tuning one model on everything?
**Answer:** Heterogeneous remote sensing tasks require fundamentally different inductive biases:
- **Temporal change detection** requires dual-branch Siamese convolutional feature subtraction at pixel resolution.
- **Optical + SAR corroboration** requires physical radar cross-section analysis ($\sigma^0$ backscatter) cross-referenced with optical multispectral indices.
- **Visual Question Answering** requires tokenized vision-language transformer reasoning.
By decoupling perception heads, SatQuery achieves higher task precision, modular upgradeability, and strict execution under an 8 GB VRAM budget via sequential eviction.

---

### Q3: What happens when a model checkpoint isn't resident or available?
**Answer:** SatQuery enforces **Rule Zero (Zero False Completeness)**: it never hallucinates or disguises offline fallbacks as neural inference. When weights are offline, the backend systematically sets:
```json
{
  "is_real_weights": false,
  "fallback_used": true,
  "execution_mode": "offline_fallback"
}
```
The frontend explicitly renders an **`OFFLINE FALLBACK MODE`** badge and displays transparent explanatory diagnostics.

---

### Q4: How is surface area ($m^2$ and hectares) calculated?
**Answer:** Area is calculated through a deterministic geometric pipeline:
1. Model binary masks are polygonized via OpenCV `findContours`.
2. Pixel vertices $(p_x, p_y)$ are transformed to geodetic coordinates $(x, y)$ via the GeoTIFF's 6-element affine geotransform matrix.
3. Coordinates in WGS84 (EPSG:4326) are dynamically reprojected to the appropriate local **metric projected UTM CRS** (e.g. `EPSG:32643` for Bangalore) via PyProj.
4. Shapely calculates the projected polygon area in square meters ($m^2$) and converts to hectares ($1\text{ ha} = 10,000\text{ m}^2$).  
*SatQuery NEVER calculates area directly in lat/lon degree units.*

---

### Q5: Is optical-SAR fusion learned or deterministic?
**Answer:** In the current production baseline, optical + SAR is implemented as **Deterministic Optical + SAR Spectral Corroboration**. Sentinel-2 optical spectral indices (RGB/NDWI) are cross-examined against Sentinel-1 C-band SAR radar backscatter intensity ($\sigma^0$ in dB) to compute quantitative decision concordance ($1.0 - 2 \cdot |\Delta f|$). It is transparently labeled as corroboration, avoiding unsubstantiated claims of learned latent fusion when foundation ViT weights are not resident.

---

### Q6: How do you prevent hallucinated spatial coordinates?
**Answer:** Coordinate hallucination is prevented by anchoring all geometry to the ingested raster's native georeferencing metadata:
- Neural grounding heads only output normalized bounding box ratios $[0.0, 1.0]$.
- These ratios are strictly mapped through the raster's native GDAL affine transform $[a, b, c, d, e, f]$ and validated against the scene's bounding box.
- The LLM never invents geographic latitudes or longitudes.

---

### Q7: How is change percentage calculated?
**Answer:** Change percentage is calculated directly from the raw Siamese ChangeNet sigmoid probability tensor:
$$\text{Change \%} = \frac{\sum \mathbb{I}(P_{\text{change}}(x, y) > 0.5)}{H \times W} \times 100$$
It represents the fraction of pixels exceeding the $50\%$ change certainty threshold within the co-registered scene extent.

---

### Q8: How does the system handle invalid, corrupt, or unsupported imagery?
**Answer:** Multi-layer validation gates protect the backend:
- `validate_file_path` enforces a 500 MB size limit and strict extension whitelisting (`.tif`, `.tiff`, `.geotif`, `.png`, `.jpg`).
- Path traversal sequences (`../`, encoded escapes) are rejected with HTTP 400.
- Missing CRS is detected and reported as `unprojected` without crashing.
- Single-image submissions for temporal change or optical-SAR fusion are rejected gracefully with constructive error messages.

---

### Q9: Can SatQuery operate completely offline?
**Answer:** Yes. SatQuery AI is 100% self-contained and offline-capable:
- Pre-seeded with 4 canonical ISRO demonstration scenarios (*Bangalore Urban Expansion*, *Brahmaputra Flood Dynamics*, *Sundarbans Mangrove Delta*, *Thar Canal*).
- Uses local SQLite database and local disk asset caching.
- Requires zero external cloud API keys or internet connections for standard operation.

---

### Q10: How does SatQuery prevent Out-Of-Memory (OOM) crashes on an 8 GB GPU?
**Answer:** Through **Sequential GPU Model Management** in `backend/models/manager.py`:
- Only one large model is loaded into VRAM at any given instant.
- Before loading a new specialist head, `gpu_manager.unload_active()` calls `del model`, `del tokenizer`, and `torch.cuda.empty_cache()`.
- GeoChat-7B in 4-bit NF4 consumes $\approx 4.5\text{ GB}$ VRAM; ChangeNet consumes $\approx 180\text{ MB}$.
- Peak VRAM footprint never exceeds $4.65\text{ GB}$, comfortably within the 8 GB VRAM budget of an RTX 4060 Laptop GPU.
