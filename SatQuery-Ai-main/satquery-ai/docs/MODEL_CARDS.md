# SatQuery AI — Scientific Model Cards

**SIH26167 · Indian Space Research Organisation (ISRO) · Space Technology Theme**  
**Standards:** Full Architectural Transparency · Parameter Budgets · Explicit Fallback Disclosures  

---

## 1. GeoChat-7B (Remote Sensing Vision-Language Specialist)

```
==========================================================================
MODEL CARD: GeoChat-7B (4-bit NF4 Quantized)
==========================================================================
MODEL NAME:        GeoChat-7B
VERSION:           v1.0-4bit
ARCHITECTURE:      LLaVA-style Vision-Language Model (Vicuna-7B LLM + CLIP-ViT-L/14)
TASK CAPABILITIES: Single-Image RS-VQA, Scene Captioning, Visual Grounding
PARAMETER COUNT:   7.0 Billion Parameters
PRECISION:         4-bit NormalFloat (NF4) via BitsAndBytes Quantization
TARGET HARDWARE:   NVIDIA RTX 4060 Laptop (8 GB VRAM) — Resident Footprint: ~4.5 GB
INPUT DATA:        GeoTIFF / TIFF RGB/Multispectral Rasters (2nd–98th percentile normalized)
OUTPUT FORMAT:     Natural language text tokens + Normalized bounding boxes [ymin, xmin, ymax, xmax]
WEIGHTS STATUS:    Available on Hugging Face (`MBZUAI/geochat-7b`). Downloadable on demand via
                   `python scripts/download_geochat.py`.
FALLBACK PROTOCOL: Explicit `[Development / Offline Mode]` tagged with `is_real_weights: false`
                   and `fallback_used: true` when model weights are not loaded.
==========================================================================
```

### Downstream Pipeline Flow
$$\text{GeoTIFF} \to \text{Rasterio Band Stats} \to \text{Dynamic Contrast Stretch} \to \text{GeoChat Processor} \to \text{4-bit VLM} \to \text{BBox } [y_{\min}, x_{\min}, y_{\max}, x_{\max}] \to \text{Affine Head} \to \text{UTM Polygon Area } (m^2, \text{ha})$$

---

## 2. Siamese ChangeNet (Bi-Temporal Change Detection Specialist)

```
==========================================================================
MODEL CARD: Siamese ChangeNet (Dual-Branch 2D CNN)
==========================================================================
MODEL NAME:        Siamese ChangeNet
VERSION:           v1.0-PyTorch
ARCHITECTURE:      Siamese Dual-Branch Deep Convolutional Neural Network with Residual Skip Connections
TASK CAPABILITIES: Bi-Temporal Surface Change Detection, Probability Tensor Generation
PARAMETER COUNT:   1.8 Million Parameters
PRECISION:         FP32 / FP16 PyTorch Tensor
TARGET HARDWARE:   CUDA GPU / CPU — Resident Footprint: ~180 MB VRAM
INPUT DATA:        Paired Co-Registered Rasters ($T_1$ Before, $T_2$ After) resized to 256×256
OUTPUT FORMAT:     2D Sigmoid Probability Tensor $\in [0.0, 1.0]^{256 \times 256}$
DOWNSTREAM HEAD:   Thresholded at $>0.5 \to$ OpenCV `findContours` $\to$ Topological Polygons $\to$
                   Projected UTM Reprojection $\to$ Metric Area ($m^2$, ha)
TRAINING PIPELINE: Trainable via `scripts/train_changenet_synthetic.py` (saves `checkpoints/changenet_best.pt`)
==========================================================================
```

### Downstream Pipeline Flow
$$T_1 + T_2 \to \text{ORB/RANSAC IoU} \to \text{ChangeNet Dual Branch} \to \text{Sigmoid Tensor } (>0.5) \to \text{OpenCV Contours} \to \text{Shapely Metric UTM} \to \text{GeoJSON Features } + \text{Area } (m^2, \text{ha})$$

---

## 3. DOFA Multimodal Specialist (Optical + SAR Corroboration)

```
==========================================================================
MODEL CARD: DOFA Specialist (Optical Spectral + Sentinel-1 SAR Corroboration)
==========================================================================
MODEL NAME:        DOFA Multimodal Specialist
VERSION:           v1.0-SpectralSAR
METHOD:            Deterministic Optical Spectral Divergence + SAR C-band $\sigma^0$ dB Corroboration
LEARNED FUSION:    NO (When foundation ViT weights are offline)
CORROBORATION:     YES (Quantitative Decision Concordance Metric)
INPUT SENSORS:     Sentinel-2 Optical (RGB/NIR) + Sentinel-1 SAR (C-band VV/VH)
OPTICAL FEATURES:  Green-Red Spectral Ratio, NDWI Proxy, 3-Band Mean/Variance
SAR FEATURES:      Radar Backscatter Intensity $\sigma^0$ (in dB), Low-Backscatter Fraction ($<-20\text{ dB}$)
CONCORDANCE SCORE: $\text{Concordance} = 1.0 - 2 \cdot |f_{\text{water}}^{\text{optical}} - f_{\text{low\_backscatter}}^{\text{sar}}|$
PROVENANCE LABEL:  "Deterministic Optical + SAR Spectral Corroboration"
==========================================================================
```

### Downstream Pipeline Flow
$$\text{Optical S2} + \text{SAR S1} \to \text{Rasterio Band Extraction} \to \text{Spectral Divergence} + \text{SAR } \sigma^0\text{ dB Analysis} \to \text{Concordance Metric} \to \text{Cross-Modal Evidence Layer}$$
