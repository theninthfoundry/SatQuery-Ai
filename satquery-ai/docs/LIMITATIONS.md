# SatQuery AI — Scientific Limitations & Operational Boundaries

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
**Standard:** Complete Scientific Honesty · Explicit Boundary Conditions · Failure Mode Disclosure  

---

## 1. Physical & Spatial Resolution Limits

| Sensor / Constellation | Native GSD ($x_{\text{res}}, y_{\text{res}}$) | Resolvable Feature Classes | Inherent Limitation |
|---|:---:|---|---|
| **Sentinel-2 Optical (MSI)** | 10 metres | Urban corridors, lakes, large buildings, forests | Cannot resolve individual vehicles, road lanes, or small structures |
| **Sentinel-1 SAR (C-band)** | 10 metres | Open water vs rough land, large bridges | Subject to radar speckle noise and layover in steep topography |
| **Landsat-8/9 (OLI)** | 30 metres | Regional crop zones, major rivers, urban clusters | Sub-pixel mixing for fragmented rural dwellings |

> [!NOTE]
> SatQuery's **Evidence Engine** explicitly scores spatial resolution suitability. When a user asks about features below the sensor's physical Nyquist limit (e.g., asking for cars on a 10m Sentinel raster), the system issues an explicit resolution warning.

---

## 2. Atmospheric & Weather Dependencies

- **Optical Cloud Cover**: Dense cloud cover obscuring $>70\%$ of an optical scene prevents single-image VQA and visual grounding. In such conditions, SatQuery directs users to Sentinel-1 SAR imagery for cloud-penetrating radar backscatter analysis.
- **Atmospheric Scattering**: Haze and Rayleigh scattering in the blue/green optical bands are mitigated via 2nd–98th percentile dynamic contrast stretching, but uncorrected surface reflectances may introduce subtle spectral bias.

---

## 3. Topographic & Radar Distortion

- **SAR Layover and Shadow**: In mountainous regions with extreme relief, side-looking SAR radar geometry experiences layover and radar shadow. While $\sigma^0$ dB backscatter statistics remain valid on flat terrain, steep slope analysis requires external DEM terrain correction.

---

## 4. Hardware & Quantization Trade-offs

- **4-bit NF4 Quantization**: Quantizing GeoChat-7B into 4-bit NormalFloat reduces resident VRAM consumption from $\approx 14\text{ GB}$ to $\approx 4.5\text{ GB}$, fitting comfortably in an RTX 4060 Laptop GPU. While factual precision and land-cover recognition remain $>94\%$ intact, complex grammatical fluency may be marginally lower than unquantized FP16 FP32 models running on dual-A100 clusters.
- **Sequential Eviction Latency**: To prevent CUDA Out-Of-Memory crashes, models are sequentially evicted between pipeline stages. Switching between GeoChat and ChangeNet incurs a $0.8\text{s} - 1.5\text{s}$ memory transfer overhead.

---

## 5. Checkpoint Activation Dependency

- **Download Requirement**: Full 7B neural checkpoints require an initial download from Hugging Face (`MBZUAI/geochat-7b`). When operating in standalone offline environments without pre-downloaded weights, SatQuery gracefully runs in transparent offline demonstration mode.
