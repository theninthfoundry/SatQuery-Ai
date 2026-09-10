# SatQuery AI — 19-Stage Compound Golden Mission Specification

## Query
> **"Between T1 and T2, identify newly developed built-up areas, calculate the changed ground area, and corroborate the finding with SAR."**

---

## 1. Complete 19-Stage Execution Chain

```
Natural Language Query
       ↓ [Stage 01]
Intent Classification & Router
       ↓ [Stage 02]
MissionSpec Generation
       ↓ [Stage 03]
Asset Resolution & Path Validation
       ↓ [Stage 04]
CRS Inspection & Reprojection
       ↓ [Stage 05]
Co-Registration (ORB/AKAZE Keypoints + RANSAC Homography)
       ↓ [Stage 06]
Optical Bi-Temporal Change Probability (Siamese ChangeNet)
       ↓ [Stage 07]
Adaptive Otsu Thresholding
       ↓ [Stage 08]
Morphological Dilation & Erosion Noise Suppression
       ↓ [Stage 09]
Connected Components Clustering
       ↓ [Stage 10]
Affine Pixel-to-Geographic Polygonization
       ↓ [Stage 11]
WGS84 Geodesic Physical Area & Perimeter Calculation
       ↓ [Stage 12]
Spectral Index Delta Quantification (ΔNDBI, ΔNDVI, ΔNDWI)
       ↓ [Stage 13]
Sentinel-1 SAR Radiometric Calibration to σ⁰ (dB)
       ↓ [Stage 14]
5x5 Lee Speckle Noise Filter
       ↓ [Stage 15]
SAR Urban Double-Bounce Thresholding
       ↓ [Stage 16]
Level 2 Spatial Intersection (Mutual Agreement IoU & Consensus)
       ↓ [Stage 17]
Multi-Sensor Discordance Diagnostics
       ↓ [Stage 18]
Evidence Gate (Epistemological Evaluation: ANSWER / QUALIFY / ABSTAIN)
       ↓ [Stage 19]
Canonical EvidenceContract Generation & Multi-Format Dossiers (PDF, GeoJSON, CSV, JSON)
```

---

## 2. Verification Execution

To execute and verify the canonical Golden Mission:
```bash
python scripts/run_golden_mission.py
```

Expected quantitative output:
- **Altered Extent**: 18.46%
- **Physical Measured Area**: 1,398,770.2 m² (139.877 ha / 1.3988 km²)
- **SAR Corroboration IoU**: 0.00 (Honest discordance detection)
- **Evidence Gate**: QUALIFY (Confidence: 0.792)
- **Execution Time**: ~600 - 800 ms
- **Generated Artifacts**:
  - `experiments/E003_compound_golden_mission/mission_result.json`
  - `/api/v1/reports/msn_golden_.../pdf`
  - `/api/v1/reports/msn_golden_.../geojson`
  - `/api/v1/reports/msn_golden_.../csv`
