# SatQuery AI — Neural Model Activation Guide

**Target Hardware:** Single NVIDIA RTX 4060 Laptop GPU (8 GB VRAM) / CUDA 12.1+ / CPU Fallback  
**Frameworks:** PyTorch 2.2+, Transformers 4.38+, BitsAndBytes 0.43+, GDAL / Rasterio  

---

## 1. GeoChat-7B (4-bit NF4 Quantization)

### Architecture
- **Base Architecture:** LLaVA-style Vision-Language Model (Vicuna-7B LLM + CLIP-ViT-L/14 vision encoder).
- **Quantization Target:** 4-bit NormalFloat (`load_in_4bit=True, bnb_4bit_quant_type="nf4"`).
- **Resident VRAM Footprint:** $\approx 4,450\text{ MB}$.

### Activation Command
```bash
python scripts/download_geochat.py
```

*This downloads the model checkpoint from Hugging Face (`MBZUAI/geochat-7b`) into `./checkpoints/geochat/`.*

### Verification Check
When weights are resident on disk:
```json
{
  "model_name": "GeoChat-7B",
  "model_version": "v1.0-4bit",
  "weights_available": true,
  "is_real_weights": true,
  "fallback_used": false,
  "execution_mode": "real_inference",
  "device": "cuda:0",
  "quantization": "4-bit NF4",
  "checkpoint_path": "checkpoints/geochat"
}
```

### Standalone Python Verification Script
```python
from backend.models.geochat import geochat_adapter

# Load into 4-bit CUDA memory
geochat_adapter.load(device="cuda:0")

# Test VQA inference
result = geochat_adapter.vqa(
    image_path="data/uploads/bangalore_2024.tif",
    question="Describe the dominant land cover in this scene.",
)
print("VQA Output:", result)

# Test Visual Grounding inference
grounding = geochat_adapter.ground(
    image_path="data/uploads/bangalore_2024.tif",
    referring_expression="water body",
)
print("Grounding Boxes:", grounding)

# Evict model from VRAM
geochat_adapter.unload()
```

---

## 2. Siamese ChangeNet (Dual-Branch 2D CNN)

### Architecture
- **Architecture:** Siamese Dual-Branch Convolutional Neural Network with differential residual blocks.
- **VRAM Footprint:** $\approx 180\text{ MB}$.
- **Output:** 2D Sigmoid Probability Map $\in [0.0, 1.0]^{256 \times 256}$.

### Training & Checkpoint Generation
```bash
python scripts/train_changenet_synthetic.py
```
*Trains for 10 epochs on synthetic paired satellite scenes and saves `checkpoints/changenet_best.pt`.*

---

## 3. DOFA Multimodal Specialist (Optical + SAR Corroboration)

### Architecture
- **Mode:** Deterministic Optical Spectral Divergence + Sentinel-1 C-band SAR $\sigma^0$ dB Backscatter Analysis.
- **VRAM Footprint:** CPU / GPU $<100\text{ MB}$.
- **Cross-Modal Decision Concordance Formula:**
  $$\text{Concordance} = 1.0 - 2 \cdot |f_{\text{water}}^{\text{optical}} - f_{\text{low\_backscatter}}^{\text{sar}}|$$
