# SatQuery AI — Evidence Policy & Epistemological Decision Framework

## 1. Core Principles

1. **Zero Fabrication**: No coordinates, polygons, areas, confidence scores, model statuses, timings, or benchmark results may ever be hardcoded or fabricated.
2. **Three Non-Interchangeable Concepts**:
   - **Model Confidence** (`model_confidence: number | null`): What the neural model believes based on training distribution and calibrated logits.
   - **Physical Measurement** (`measurement: { value, unit, method, provenance }`): What deterministic GIS calculations produced across real ground pixels on the WGS84 ellipsoid.
   - **Evidence Reliability** (`reliability: { score, factors, decision }`): How trustworthy the scientific conclusion is across multi-sensor agreement, co-registration error, spatial overlap, cloud contamination, and spatial resolution suitability.

---

## 2. Evidence Gate Decision Policy

Every analytical mission evaluated by SatQuery AI must pass through the **Evidence Gate** (`backend/evidence/gate.py`), which yields exactly one of three epistemological decisions:

### `ANSWER`
- **Criteria**:
  - Registration RMSE ≤ 1.5 pixels
  - Cloud contamination ≤ 15.0%
  - Spatial Overlap IoU ≥ 0.70
  - Sensor Agreement / Corroboration ≥ 0.60
  - Physical area measured with valid CRS on WGS84 ellipsoid
- **Action**: Unconditional assertion of finding with full supporting telemetry.

### `QUALIFY`
- **Criteria**:
  - Registration RMSE > 1.5 px or minor geometric boundary uncertainty
  - Partial cloud contamination (15% - 35%)
  - Multi-sensor discordance (e.g. Optical detected change where SAR backscatter remained calm)
  - Untrained baseline model active (`classical_fallback` mode)
- **Action**: Finding is asserted with prominent scientific caveats explicitly explaining which factors require analyst review.

### `ABSTAIN`
- **Criteria**:
  - Registration failure (RMSE > 5.0 pixels or co-registration aborted)
  - Severe cloud obscuration (> 50% cloud cover over AOI)
  - Spatial overlap IoU < 0.20 (incompatible scenes)
  - Missing or corrupted CRS coordinates
  - Insufficient valid pixels to support an analytical conclusion
- **Action**: System declares: *"Insufficient evidence to support this conclusion."* Emits no plausible-looking fake polygons or fabricated answers.

---

## 3. Reliability Multi-Factor Formula

The composite reliability score $R \in [0.0, 1.0]$ is computed deterministically:

$$R = w_{\text{reg}} F_{\text{reg}} + w_{\text{overlap}} F_{\text{overlap}} + w_{\text{cloud}} F_{\text{cloud}} + w_{\text{sensor}} F_{\text{sensor}} + w_{\text{gsd}} F_{\text{gsd}}$$

Where default weights sum to 1.0:
- $w_{\text{reg}} = 0.25$ (Coregistration quality)
- $w_{\text{overlap}} = 0.25$ (Spatial bounding box intersection)
- $w_{\text{cloud}} = 0.20$ ($1.0 - \text{Cloud Fraction}$)
- $w_{\text{sensor}} = 0.20$ (Optical-SAR spatial consensus ratio)
- $w_{\text{gsd}} = 0.10$ (Ground sample distance suitability)

---

## 4. Truth States

Every model or analysis operation explicitly reports its truth state:
- `REAL_MODEL`: Production weights loaded, checksum verified, real inference executed.
- `TRAINED_MODEL`: Checkpoint trained on domain dataset (e.g. LEVIR-CD, RSVQA).
- `UNTRAINED_MODEL`: Architectural backbone instantiable but weights untrained; emits explicit notice.
- `CLASSICAL_FALLBACK`: Deterministic spectral differential (ΔNDBI, ΔNDVI, ΔNDWI) or physics-based Lee filter executed.
- `PARTIAL`: Multi-sensor mission where one modality succeeded and another was unavailable.
- `FAILED`: Explicit abort due to data quality or corruption; zero synthetic substitutes.
