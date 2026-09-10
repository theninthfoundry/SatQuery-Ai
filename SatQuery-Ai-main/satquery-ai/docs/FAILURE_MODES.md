# SatQuery AI — Failure Engineering & Honest Fallback States

## 1. Zero-Deception Philosophy

Under no circumstances does SatQuery AI silently substitute demo data, invent coordinates, or forge high confidence scores when an operation fails. Every failure produces an explicit, user-facing epistemological state.

---

## 2. Tested Failure Modes & System Responses

### 1. Missing or Uninstalled Neural Checkpoint (e.g. GeoChat-7B, SAM)
- **Runtime Response**: Explicit disclosure.
- **Truth State**: `CLASSICAL_FALLBACK`
- **Notice**: *"Neural checkpoint unavailable on disk. Classical spectral-spatial fallback executed."*
- **EvidenceContract**: `execution_mode: "classical_fallback"`, `is_real_weights: false`.

### 2. Incompatible Scene Spatial Resolution
- **Runtime Response**: CompatibilityEngine flags resolution ratio violation ($R_{\text{ratio}} > 3.0$).
- **Notice**: *"Scenes cannot be compared directly because spatial resolution differs significantly (10 m vs 60 m). Resampling required."*

### 3. Severe Cloud Contamination (> 50% cloud cover over AOI)
- **Runtime Response**: Evidence Gate activates `ABSTAIN` policy.
- **Notice**: *"Insufficient cloud-free pixels to support an analytical conclusion. Observation contains 68.4% cloud cover."*
- **Result**: Zero fabricated polygons emitted.

### 4. Co-Registration Failure (Failed Feature Matching / RMSE > 5 px)
- **Runtime Response**: Geometric registration aborts or emits warning.
- **Notice**: *"Co-registration failed: insufficient distinctive keypoint matches between T1 and T2 scenes."*
- **Evidence Gate**: `ABSTAIN` or `QUALIFY` with degraded reliability factor ($F_{\text{reg}} < 0.20$).

### 5. Malformed Geometry & Zip Slip Attack
- **Runtime Response**: `InputSanitizer` and `AOIImporter` catch path traversal (`../`) and compression traps.
- **Notice**: *"Security rejection: Archive contains illegal traversal path or exceeds decompression budget."*
- **HTTP Status**: 422 Unprocessable Entity.

### 6. Missing or Corrupted Coordinate Reference System (CRS)
- **Runtime Response**: `inspect_crs` flags invalid CRS.
- **Notice**: *"Raster lacks georeferencing metadata (missing CRS). Coordinates cannot be projected to WGS84 ellipsoid."*
- **Status**: Invalid asset; area calculation refused until georeferenced.
