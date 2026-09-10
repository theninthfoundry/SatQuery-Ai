"""Semantic Change Classification Engine.

Transforms binary change masks into physically meaningful Earth Observation
land-cover transitions using spectral index deltas (ΔNDVI, ΔNDBI, ΔNDWI)
and SAR backscatter changes (Δσ⁰).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ChangeCategory(str, Enum):
    """Categorization of remote sensing land-cover transitions."""
    NEW_URBAN_BUILTUP = "new_urban_builtup"        # Green/bare → buildings, roads
    VEGETATION_CLEARING = "vegetation_clearing"    # Forest/crop loss, deforestation
    REVEGETATION_GROWTH = "revegetation_growth"    # Crop emergence, afforestation
    WATER_BODY_EXPANSION = "water_expansion"       # Inundation, reservoir fill
    WATER_BODY_RECESSION = "water_recession"       # Drought, dry lakebed
    SOIL_EXCAVATION = "soil_excavation"            # Mining, earthwork
    INFRASTRUCTURE_DEMOLITION = "demolition"       # Built-up loss
    UNCLASSIFIED_CHANGE = "unclassified_change"
    NO_CHANGE = "no_change"


@dataclass
class CategoryBreakdown:
    """Quantitative measurement for a specific change category."""
    category: ChangeCategory
    pixel_count: int
    percentage_of_total: float
    percentage_of_changed: float
    area_m2: Optional[float] = None
    area_hectares: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "category_name": self.category.value.replace("_", " ").title(),
            "pixel_count": self.pixel_count,
            "percentage_of_total": round(self.percentage_of_total, 3),
            "percentage_of_changed": round(self.percentage_of_changed, 2),
            "area_m2": round(self.area_m2, 2) if self.area_m2 is not None else None,
            "area_hectares": round(self.area_hectares, 3) if self.area_hectares is not None else None,
        }


@dataclass
class SemanticChangeResult:
    """Full semantic change detection report."""
    total_pixels: int
    changed_pixels: int
    overall_change_percentage: float
    dominant_transition: ChangeCategory
    breakdown: List[CategoryBreakdown]
    semantic_change_map: Optional[np.ndarray] = None  # (H, W) uint8 with category codes
    pixel_size_meters: Optional[float] = None
    summary_text: str = ""

    def to_dict(self, include_map: bool = False) -> Dict[str, Any]:
        res = {
            "total_pixels": self.total_pixels,
            "changed_pixels": self.changed_pixels,
            "overall_change_percentage": round(self.overall_change_percentage, 2),
            "dominant_transition": self.dominant_transition.value,
            "categories": [b.to_dict() for b in self.breakdown],
            "summary": self.summary_text,
        }
        if include_map and self.semantic_change_map is not None:
            res["map_shape"] = list(self.semantic_change_map.shape)
        return res


class SemanticChangeClassifier:
    """Classifies binary change pixels into semantic land cover transition classes."""

    # Categorical codes for output raster
    CATEGORY_CODES = {
        ChangeCategory.NO_CHANGE: 0,
        ChangeCategory.NEW_URBAN_BUILTUP: 1,
        ChangeCategory.VEGETATION_CLEARING: 2,
        ChangeCategory.REVEGETATION_GROWTH: 3,
        ChangeCategory.WATER_BODY_EXPANSION: 4,
        ChangeCategory.WATER_BODY_RECESSION: 5,
        ChangeCategory.SOIL_EXCAVATION: 6,
        ChangeCategory.INFRASTRUCTURE_DEMOLITION: 7,
        ChangeCategory.UNCLASSIFIED_CHANGE: 8,
    }

    def classify_changes(
        self,
        change_mask: np.ndarray,
        delta_ndvi: Optional[np.ndarray] = None,
        delta_ndbi: Optional[np.ndarray] = None,
        delta_ndwi: Optional[np.ndarray] = None,
        delta_sar_db: Optional[np.ndarray] = None,
        pixel_size_meters: Optional[float] = None,
    ) -> SemanticChangeResult:
        """Classify changed pixels into domain-specific transition categories.
        
        Args:
            change_mask: (H, W) boolean or 0/1 array indicating detected change.
            delta_ndvi: (H, W) float array: NDVI_T2 - NDVI_T1.
            delta_ndbi: (H, W) float array: NDBI_T2 - NDBI_T1 (built-up index).
            delta_ndwi: (H, W) float array: NDWI_T2 - NDWI_T1 (water index).
            delta_sar_db: (H, W) float array: SAR_T2 - SAR_T1 in dB.
            pixel_size_meters: Ground resolution for area calculation.
        """
        is_changed = (change_mask > 0)
        h, w = is_changed.shape
        total_pixels = int(is_changed.size)
        n_changed = int(np.sum(is_changed))

        semantic_map = np.zeros((h, w), dtype=np.uint8)
        if n_changed == 0:
            return SemanticChangeResult(
                total_pixels=total_pixels,
                changed_pixels=0,
                overall_change_percentage=0.0,
                dominant_transition=ChangeCategory.NO_CHANGE,
                breakdown=[],
                semantic_change_map=semantic_map,
                pixel_size_meters=pixel_size_meters,
                summary_text="No significant land cover change detected within the observation window.",
            )

        def _match_shape(arr: Optional[np.ndarray]) -> np.ndarray:
            if arr is None:
                return np.zeros((h, w), dtype=np.float32)
            if arr.shape == (h, w):
                return arr.astype(np.float32)
            try:
                import cv2
                return cv2.resize(arr.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
            except Exception:
                from PIL import Image as _PIL
                return np.asarray(_PIL.fromarray(arr.astype(np.float32)).resize((w, h)), dtype=np.float32)

        d_ndvi = _match_shape(delta_ndvi)
        d_ndbi = _match_shape(delta_ndbi)
        d_ndwi = _match_shape(delta_ndwi)
        d_sar = _match_shape(delta_sar_db)

        # 1. Decision logic for change categories
        c_new_builtup = is_changed & (
            (d_ndbi > 0.08) | ((d_sar > 2.5) & (d_ndvi < 0.05))
        )
        c_veg_clear = is_changed & (~c_new_builtup) & (d_ndvi < -0.15)
        c_revegetation = is_changed & (~c_new_builtup) & (d_ndvi > 0.15)
        c_water_exp = is_changed & (~c_new_builtup) & (~c_veg_clear) & (
            (d_ndwi > 0.12) | (d_sar < -3.0)
        )
        c_water_rec = is_changed & (~c_new_builtup) & (~c_revegetation) & (d_ndwi < -0.12)
        c_soil_excav = is_changed & (~c_new_builtup) & (~c_veg_clear) & (~c_water_exp) & (
            (d_ndvi < -0.10) & (d_ndbi > 0.0) & (d_ndbi < 0.15)
        )

        assigned = c_new_builtup | c_veg_clear | c_revegetation | c_water_exp | c_water_rec | c_soil_excav
        c_unclassified = is_changed & (~assigned)

        # Populate output raster
        semantic_map[c_new_builtup] = self.CATEGORY_CODES[ChangeCategory.NEW_URBAN_BUILTUP]
        semantic_map[c_veg_clear] = self.CATEGORY_CODES[ChangeCategory.VEGETATION_CLEARING]
        semantic_map[c_revegetation] = self.CATEGORY_CODES[ChangeCategory.REVEGETATION_GROWTH]
        semantic_map[c_water_exp] = self.CATEGORY_CODES[ChangeCategory.WATER_BODY_EXPANSION]
        semantic_map[c_water_rec] = self.CATEGORY_CODES[ChangeCategory.WATER_BODY_RECESSION]
        semantic_map[c_soil_excav] = self.CATEGORY_CODES[ChangeCategory.SOIL_EXCAVATION]
        semantic_map[c_unclassified] = self.CATEGORY_CODES[ChangeCategory.UNCLASSIFIED_CHANGE]

        # 2. Compile metrics per category
        cats = [
            (ChangeCategory.NEW_URBAN_BUILTUP, int(np.sum(c_new_builtup))),
            (ChangeCategory.VEGETATION_CLEARING, int(np.sum(c_veg_clear))),
            (ChangeCategory.REVEGETATION_GROWTH, int(np.sum(c_revegetation))),
            (ChangeCategory.WATER_BODY_EXPANSION, int(np.sum(c_water_exp))),
            (ChangeCategory.WATER_BODY_RECESSION, int(np.sum(c_water_rec))),
            (ChangeCategory.SOIL_EXCAVATION, int(np.sum(c_soil_excav))),
            (ChangeCategory.UNCLASSIFIED_CHANGE, int(np.sum(c_unclassified))),
        ]

        # Filter out 0 counts
        area_factor = (pixel_size_meters ** 2) if pixel_size_meters else None
        breakdown: List[CategoryBreakdown] = []
        for cat, count in sorted(cats, key=lambda x: x[1], reverse=True):
            if count > 0:
                area_m2 = count * area_factor if area_factor else None
                area_ha = (area_m2 / 10000.0) if area_m2 else None
                breakdown.append(CategoryBreakdown(
                    category=cat,
                    pixel_count=count,
                    percentage_of_total=(count / max(1, total_pixels)) * 100.0,
                    percentage_of_changed=(count / max(1, n_changed)) * 100.0,
                    area_m2=area_m2,
                    area_hectares=area_ha,
                ))

        dominant = breakdown[0].category if breakdown else ChangeCategory.UNCLASSIFIED_CHANGE
        overall_pct = (n_changed / max(1, total_pixels)) * 100.0

        # 3. Narrative synthesis
        dom_name = dominant.value.replace("_", " ")
        dom_pct = breakdown[0].percentage_of_changed if breakdown else 0.0
        summary = (
            f"Detected surface changes across {overall_pct:.2f}% of AOI ({n_changed:,} pixels). "
            f"The primary driver of change is {dom_name}, accounting for {dom_pct:.1f}% "
            f"of all detected land-cover transitions."
        )

        return SemanticChangeResult(
            total_pixels=total_pixels,
            changed_pixels=n_changed,
            overall_change_percentage=overall_pct,
            dominant_transition=dominant,
            breakdown=breakdown,
            semantic_change_map=semantic_map,
            pixel_size_meters=pixel_size_meters,
            summary_text=summary,
        )
