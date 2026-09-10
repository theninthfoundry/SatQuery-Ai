# SatQuery AI — Hardware Profile & Constraints

This document specifies the target hardware profile, runtime environment, and operational constraints for SatQuery AI.

---

## 1. System Specifications

| Component | Target Specification | Status / Notes |
|---|---|---|
| **OS** | Windows 11 (64-bit) / Linux (Ubuntu 22.04 LTS) | Multi-platform compatible backend |
| **CPU** | Intel Core i7 / AMD Ryzen 7 (8+ cores) | Used for geospatial raster decoding & preprocessing |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU | Target hardware envelope |
| **VRAM** | ~8,192 MB (8 GB GDDR6) | **Hard Constraint**: Maximum resident GPU allocation |
| **CUDA Runtime** | CUDA 12.1+ / 12.2 / 12.4 | Supported via PyTorch CUDA wheels |
| **System RAM** | 16 GB - 32 GB DDR5 | Used for in-memory raster caching & windowed reads |
| **Storage** | 512 GB+ NVMe SSD | Fast I/O for GeoTIFF tiling and preview generation |
| **Python** | Python 3.10 / 3.11 / 3.12 | Standard virtual environment |
| **Node.js** | Node.js 18.x / 20.x LTS + npm | Next.js frontend runtime |

---

## 2. GPU Memory Budget & Allocation Strategy

Under the **8 GB VRAM** ceiling:

```text
Total VRAM: ~8.0 GB
├── System & CUDA Context Overhead:   ~0.8 GB
├── Peak Working Memory (Activations): ~1.2 GB
└── Available for Model Weights:      ~6.0 GB
```

### Key Engineering Rules for 8 GB VRAM:
1. **Sequential Model Loading**: Never keep multiple heavy models resident in VRAM simultaneously. The `GPUManager` must explicitly load, execute, and unload models, calling `torch.cuda.empty_cache()` between tasks.
2. **Quantization Strategy**:
   - VLM (e.g., GeoChat / Qwen-VL): 4-bit (BitsAndBytes NF4) or 8-bit quantization (~4.0 - 5.5 GB VRAM).
   - Change Detection Model (Siamese ResNet/U-Net): FP16 / FP32 (~0.8 GB VRAM).
   - SAR Corroborator / Backscatter Analysis: CPU / NumPy or lightweight FP16 (<0.2 GB VRAM).
3. **No Speculative Pre-loading**: Models are loaded on-demand per request intent and evicted after inference or upon model switch.
