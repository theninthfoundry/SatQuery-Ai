# SatQuery AI — Phase 1 Hardware Profile & VRAM Budget

## 1. Hardware Specification

| Parameter | Specification | Notes |
|---|---|---|
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU | Ada Lovelace Architecture |
| **VRAM** | 8,192 MB (8 GB GDDR6) | Hard physical budget constraint |
| **Compute Capability** | 8.9 | Supports FP16, BF16, Int8, and Int4 (BitsAndBytes NF4) |
| **CUDA Driver / Runtime** | CUDA 12.x | PyTorch CUDA with `device_map="auto"` |
| **Host System** | Windows 11 x64 (i7 CPU, 16+ GB System RAM) | |

---

## 2. VRAM Allocation & Sequential Execution Strategy

Because total GPU memory is capped at ~8 GB, **concurrent multi-model residence in VRAM is strictly prohibited**.

```
+-----------------------------------------------------------------------------+
|                     RTX 4060 VRAM Budget Envelope (8,192 MB)               |
+-----------------------------------------------------------------------------+
| Base PyTorch Context & CUDA Runtime: ~500 MB                                |
| Max Single Model Footprint:                                                 |
|   • GeoChat-7B (4-bit NF4 quantized):        ~4,500 MB (Peaks at ~5,200 MB) |
|   • Siamese ChangeNet (FP16/FP32):           ~800 MB                        |
|   • DOFA ViT-Base (FP16):                    ~1,200 MB                      |
| Working Tensor / KV Cache Headroom:          ~2,500 MB                      |
+-----------------------------------------------------------------------------+
```

### Sequential Model Residence Rules (Enforced by `GPUManager`):
1. **Never load two models simultaneously.**
2. When switching from `GeoChat` to `ChangeNet` or `DOFA`:
   - Invoke `model.unload()`.
   - Call `del model`.
   - Execute `torch.cuda.empty_cache()` and `torch.cuda.reset_peak_memory_stats()`.
3. Wrap all inference passes in `torch.inference_mode()` to eliminate computational graph retention overhead.
