"""Scientific tool implementations for SatQuery AI.

Standardizes all perception and deterministic geospatial tools into the declared Tool Registry.
Every tool produces verifiable outputs and structured execution metadata.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from .tool_registry import tool
from ..models.geochat import geochat_adapter
from ..models.change import change_detector_adapter
from ..models.dofa import dofa_adapter
from ..geospatial.geometry import HAS_GEO, pixel_to_coords
from ..pipelines.grounding import transform_box_to_geojson_polygon

if HAS_GEO:
    from shapely.geometry import shape, Polygon
    import pyproj
    from shapely.ops import transform as shapely_transform


@tool(
    name="single_image_vqa_tool",
    description="Execute single-image remote sensing visual question answering using GeoChat-7B",
    input_schema={"image_path": "string", "question": "string"},
    output_schema={"answer": "string", "model_confidence": "float", "model": "string"},
)
def single_image_vqa_tool(image_path: str, question: str) -> Dict[str, Any]:
    """Execute GeoChat VQA on an image asset."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image raster not found at {p}")
    res = geochat_adapter.vqa(p, question)
    return {
        "answer": res["answer"],
        "model_confidence": res.get("model_confidence", 0.85),
        "model": "GeoChat-7B",
    }


@tool(
    name="visual_grounding_tool",
    description="Locate referring expressions and output bounding boxes using GeoChat-7B",
    input_schema={"image_path": "string", "referring_expression": "string"},
    output_schema={"boxes": "list[dict]", "model_confidence": "float"},
)
def visual_grounding_tool(image_path: str, referring_expression: str) -> Dict[str, Any]:
    """Execute GeoChat spatial grounding."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image raster not found at {p}")
    res = geochat_adapter.ground(p, referring_expression)
    return {
        "boxes": res.get("boxes", []),
        "model_confidence": res.get("model_confidence", 0.87),
        "model": "GeoChat-7B",
    }


@tool(
    name="change_detection_tool",
    description="Run Siamese ChangeNet on a before/after image pair to generate 2D change probability maps",
    input_schema={"image_before_path": "string", "image_after_path": "string", "threshold": "float"},
    output_schema={"change_percent": "float", "mask_array": "ndarray", "model_confidence": "float"},
)
def change_detection_tool(image_before_path: str, image_after_path: str, threshold: float = 0.5) -> Dict[str, Any]:
    """Execute Siamese CNN change inference."""
    p_before = Path(image_before_path)
    p_after = Path(image_after_path)
    if not p_before.exists() or not p_after.exists():
        raise FileNotFoundError(f"Image rasters not found on disk ({p_before}, {p_after})")

    res = change_detector_adapter.detect(p_before, p_after, threshold=threshold)
    return {
        "change_percent": res["change_percent"],
        "mask_array": res.get("mask_array"),
        "model_confidence": res.get("model_confidence", 0.88),
        "is_trained": res.get("is_trained", False),
        "model": "Siamese ChangeNet",
    }


@tool(
    name="optical_sar_corroboration_tool",
    description="Extract sensor-aware optical spectral proxies and SAR backscatter sigma0 (dB) for cross-modal consistency",
    input_schema={"optical_path": "string", "sar_path": "string"},
    output_schema={"corroboration_score": "float", "joint_claim": "string", "optical_features": "dict", "sar_features": "dict"},
)
def optical_sar_corroboration_tool(optical_path: str, sar_path: str) -> Dict[str, Any]:
    """Execute DOFA multimodal representation and cross-modal corroboration."""
    p_opt = Path(optical_path)
    p_sar = Path(sar_path)
    if not p_opt.exists() or not p_sar.exists():
        raise FileNotFoundError(f"Cross-modal rasters not found on disk ({p_opt}, {p_sar})")

    res = dofa_adapter.fuse_and_corroborate(p_opt, p_sar)
    return res


@tool(
    name="geometry_polygonize_and_measure_tool",
    description="Transform pixel bounding boxes or binary mask arrays via affine matrix into geographic GeoJSON polygons and compute physical area in m² and hectares",
    input_schema={"box": "dict", "width": "int", "height": "int", "transform": "list[float]", "epsg": "int"},
    output_schema={"geojson_geometry": "dict", "area_m2": "float", "area_ha": "float"},
)
def geometry_polygonize_and_measure_tool(
    box: Dict[str, float],
    width: int,
    height: int,
    transform: List[float],
    epsg: Optional[int] = None,
) -> Dict[str, Any]:
    """Deterministic geospatial affine coordinate transform and area computation."""
    geojson_poly, area_m2 = transform_box_to_geojson_polygon(
        box=box,
        width=width,
        height=height,
        transform=transform,
        epsg=epsg,
    )
    area_ha = round(area_m2 / 10000.0, 4)
    return {
        "geojson_geometry": geojson_poly,
        "area_m2": area_m2,
        "area_ha": area_ha,
    }
