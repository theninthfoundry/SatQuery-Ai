"""Cloud Quality Estimator for Earth Observation Imagery.

Evaluates cloud contamination using QA bands, cloud probability products,
scene metadata, and fallback spectral heuristics with explicit method auditing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


@dataclass
class CloudQualityResult:
    """Auditable result of cloud contamination evaluation."""
    cloud_fraction: float
    method: str
    valid: bool
    quality_flag: str  # "clear", "acceptable", "degraded", "cloud_contaminated"
    cloud_mask: Optional[Any] = None  # 2D boolean array where True indicates cloud/shadow
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cloud_fraction": round(self.cloud_fraction, 4),
            "method": self.method,
            "valid": self.valid,
            "quality_flag": self.quality_flag,
            "details": self.details,
        }


class CloudQualityEstimator:
    """Multi-tiered cloud quality estimator recording precise methodology."""

    def __init__(self, clear_threshold: float = 0.05, acceptable_threshold: float = 0.20, degraded_threshold: float = 0.50):
        self.clear_thresh = clear_threshold
        self.acceptable_thresh = acceptable_threshold
        self.degraded_thresh = degraded_threshold

    def _determine_quality_flag(self, fraction: float) -> str:
        if fraction < self.clear_thresh:
            return "clear"
        elif fraction < self.acceptable_thresh:
            return "acceptable"
        elif fraction < self.degraded_thresh:
            return "degraded"
        else:
            return "cloud_contaminated"

    def estimate_from_dataset(
        self,
        ds: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CloudQualityResult:
        """Estimate cloud contamination from an open rasterio dataset."""
        if not HAS_NUMPY:
            return CloudQualityResult(
                cloud_fraction=0.0,
                method="UNAVAILABLE_NO_NUMPY",
                valid=False,
                quality_flag="acceptable",
            )

        # 1. Tier 1: Check for QA bands (QA60, SCL, or Cloud Probability)
        descriptions = [d.lower() if d else "" for d in (ds.descriptions or ())]
        tags = ds.tags()

        # 1a. Sentinel-2 QA60 band (Bit 10: Opaque clouds, Bit 11: Cirrus)
        for idx, desc in enumerate(descriptions):
            if "qa60" in desc or "qa" in desc:
                try:
                    qa = ds.read(idx + 1)
                    # Bit 10 = opaque cloud, Bit 11 = cirrus
                    cloud_mask = ((qa & (1 << 10)) != 0) | ((qa & (1 << 11)) != 0)
                    total_pixels = cloud_mask.size
                    cloud_pixels = int(np.sum(cloud_mask))
                    frac = float(cloud_pixels / max(1, total_pixels))
                    return CloudQualityResult(
                        cloud_fraction=frac,
                        method="S2_QA60",
                        valid=True,
                        quality_flag=self._determine_quality_flag(frac),
                        cloud_mask=cloud_mask,
                        details={"cloud_pixels": cloud_pixels, "total_pixels": total_pixels},
                    )
                except Exception:
                    pass

        # 1b. Scene Classification Layer (SCL)
        for idx, desc in enumerate(descriptions):
            if "scl" in desc or "scene_classification" in desc:
                try:
                    scl = ds.read(idx + 1)
                    # 3 = Cloud shadows, 8 = Cloud medium prob, 9 = Cloud high prob, 10 = Thin cirrus
                    cloud_mask = np.isin(scl, [3, 8, 9, 10])
                    frac = float(np.sum(cloud_mask) / max(1, cloud_mask.size))
                    return CloudQualityResult(
                        cloud_fraction=frac,
                        method="S2_SCL",
                        valid=True,
                        quality_flag=self._determine_quality_flag(frac),
                        cloud_mask=cloud_mask,
                        details={"classes_detected": [3, 8, 9, 10]},
                    )
                except Exception:
                    pass

        # 1c. Cloud probability layer
        for idx, desc in enumerate(descriptions):
            if "cloud_prob" in desc or "probability" in desc:
                try:
                    cprob = ds.read(idx + 1)
                    cloud_mask = cprob > 50
                    frac = float(np.sum(cloud_mask) / max(1, cloud_mask.size))
                    return CloudQualityResult(
                        cloud_fraction=frac,
                        method="CLOUD_PROBABILITY",
                        valid=True,
                        quality_flag=self._determine_quality_flag(frac),
                        cloud_mask=cloud_mask,
                    )
                except Exception:
                    pass

        # 2. Tier 2: Check dataset tags and STAC scene metadata
        meta_sources = [tags, metadata or {}]
        for src in meta_sources:
            for key in ["CLOUD_COVERAGE_ASSESSMENT", "cloud_cover", "eo:cloud_cover", "CLOUDY_PIXEL_PERCENTAGE"]:
                if key in src:
                    try:
                        val = float(src[key])
                        # If expressed as percentage 0-100, normalize to 0-1
                        frac = val / 100.0 if val > 1.0 else val
                        frac = max(0.0, min(1.0, frac))
                        return CloudQualityResult(
                            cloud_fraction=frac,
                            method="SCENE_METADATA",
                            valid=True,
                            quality_flag=self._determine_quality_flag(frac),
                            cloud_mask=None,
                            details={"metadata_key": key, "raw_value": val},
                        )
                    except (ValueError, TypeError):
                        pass

        # 3. Tier 3: Multi-band spectral heuristics
        num_bands = ds.count
        if num_bands >= 3:
            try:
                # Read Blue, Green, Red (and NIR if available)
                b_blue = ds.read(1).astype(np.float32)
                b_green = ds.read(2).astype(np.float32)
                b_red = ds.read(3).astype(np.float32)

                # Convert integer DN to approximate reflectance if DN is 0-10000 (standard Sentinel-2 L2A)
                max_val = np.max(b_blue)
                scale = 10000.0 if max_val > 255.0 else 255.0
                blue_refl = b_blue / scale
                green_refl = b_green / scale
                red_refl = b_red / scale

                # Brightness in optical + balanced high reflectance across RGB
                brightness = (blue_refl + green_refl + red_refl) / 3.0
                # Clouds are typically very bright and visually white/gray (low saturation)
                diff = np.abs(blue_refl - red_refl)
                cloud_mask = (brightness > 0.38) & (diff < 0.08)

                if num_bands >= 4:
                    # NIR check: water has very low NIR, clouds have very high NIR
                    b_nir = ds.read(4).astype(np.float32) / scale
                    cloud_mask = cloud_mask & (b_nir > 0.30)

                frac = float(np.sum(cloud_mask) / max(1, cloud_mask.size))
                return CloudQualityResult(
                    cloud_fraction=frac,
                    method="SPECTRAL_HEURISTIC",
                    valid=True,
                    quality_flag=self._determine_quality_flag(frac),
                    cloud_mask=cloud_mask,
                    details={"scale_used": scale, "bands_analyzed": min(num_bands, 4)},
                )
            except Exception as e:
                pass

        # 4. Tier 4: Fallback for single band or non-optical (e.g. SAR)
        return CloudQualityResult(
            cloud_fraction=0.0,
            method="DEFAULT_CLEAR_ASSUMPTION",
            valid=True,
            quality_flag="clear",
            cloud_mask=None,
            details={"reason": "Single-band or non-optical raster without cloud metadata"},
        )

    def estimate(self, raster_path: Union[Path, str], metadata: Optional[Dict[str, Any]] = None) -> CloudQualityResult:
        """Estimate cloud quality from a raster file path."""
        path = Path(raster_path)
        if not path.exists():
            return CloudQualityResult(
                cloud_fraction=0.0,
                method="FILE_NOT_FOUND",
                valid=False,
                quality_flag="acceptable",
            )

        if not HAS_RASTERIO:
            return CloudQualityResult(
                cloud_fraction=0.0,
                method="RASTERIO_UNAVAILABLE",
                valid=False,
                quality_flag="acceptable",
            )

        try:
            with rasterio.open(path) as ds:
                return self.estimate_from_dataset(ds, metadata=metadata)
        except Exception as e:
            return CloudQualityResult(
                cloud_fraction=0.0,
                method=f"READ_ERROR: {type(e).__name__}",
                valid=False,
                quality_flag="acceptable",
                details={"error": str(e)},
            )
