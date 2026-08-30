"""Visual grounding and spatial coordinate localization pipeline."""

import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models_db import ImageRecord, AnalysisJob
from ..models.geochat import geochat_adapter
from ..geospatial.geometry import pixel_to_coords, HAS_GEO
from ..evidence import (
    build_evidence,
    compute_vqa_confidence,
    ExecutionStep,
    EvidenceObject,
)

if HAS_GEO:
    from shapely.geometry import Polygon, mapping
    import pyproj
    from shapely.ops import transform as shapely_transform


def transform_box_to_geojson_polygon(
    box: Dict[str, float],
    width: int,
    height: int,
    transform: List[float],
    epsg: Optional[int] = None,
) -> Tuple[Dict[str, Any], float]:
    """Convert normalized bounding box [ymin, xmin, ymax, xmax] to a real-world GeoJSON polygon and compute area in m²."""
    ymin, xmin, ymax, xmax = box["ymin"], box["xmin"], box["ymax"], box["xmax"]

    # 1. Pixel corners
    px_min, px_max = xmin * width, xmax * width
    py_min, py_max = ymin * height, ymax * height

    # 2. Transform pixel corners to spatial coordinates using affine transform
    # Top-Left, Top-Right, Bottom-Right, Bottom-Left, Top-Left (closed)
    tl_x, tl_y = pixel_to_coords(px_min, py_min, transform)
    tr_x, tr_y = pixel_to_coords(px_max, py_min, transform)
    br_x, br_y = pixel_to_coords(px_max, py_max, transform)
    bl_x, bl_y = pixel_to_coords(px_min, py_max, transform)

    coords = [[
        [round(tl_x, 4), round(tl_y, 4)],
        [round(tr_x, 4), round(tr_y, 4)],
        [round(br_x, 4), round(br_y, 4)],
        [round(bl_x, 4), round(bl_y, 4)],
        [round(tl_x, 4), round(tl_y, 4)],
    ]]

    # Compute area in m²
    area_m2 = 0.0
    if HAS_GEO:
        poly = Polygon(coords[0])
        if epsg and epsg != 4326:
            # Native projected CRS (meters)
            area_m2 = round(float(poly.area), 2)
        elif epsg == 4326:
            # Lat/Lon degrees -> Reproject to Equal Area
            centroid = poly.centroid
            utm_zone = int((centroid.x + 180) / 6) + 1
            utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
            transformer = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
            projected_poly = shapely_transform(transformer.transform, poly)
            area_m2 = round(float(projected_poly.area), 2)
        else:
            # Pixel space estimate if no CRS
            area_m2 = round((px_max - px_min) * (py_max - py_min), 2)

    geojson_geom = {
        "type": "Polygon",
        "coordinates": coords,
    }

    return geojson_geom, area_m2


def run_visual_grounding_pipeline(
    image_id: str,
    referring_expression: str,
    db: Session,
) -> Dict[str, Any]:
    """Execute the end-to-end Visual Grounding pipeline, transforming boxes to real geographic polygons."""
    steps = []
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    start_total_t = time.perf_counter()

    # Step 1: Image retrieval
    t0 = time.perf_counter()
    image_row = db.get(ImageRecord, image_id)
    if not image_row:
        raise ValueError(f"Image '{image_id}' not found in database.")

    image_path = Path(image_row.path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image raster not found on disk at {image_path}")

    steps.append(
        ExecutionStep(
            step_number=1,
            tool="retrieve_image_metadata",
            description=f"Loaded raster {image_row.filename} (Affine transform & {image_row.crs or 'Local'} coordinates)",
            status="completed",
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )
    )

    # Step 2: GeoChat Visual Grounding
    t1 = time.perf_counter()
    grounding_result = geochat_adapter.ground(image_path, referring_expression)
    boxes = grounding_result.get("boxes", [])
    raw_confidence = grounding_result.get("model_confidence", 0.87)

    steps.append(
        ExecutionStep(
            step_number=2,
            tool="geochat_grounding_inference",
            description=f"Located referring expression '{referring_expression}' ({len(boxes)} bounding region detected)",
            status="completed",
            duration_ms=int((time.perf_counter() - t1) * 1000),
            model="GeoChat-7B",
            output_summary=f"Boxes: {len(boxes)}",
        )
    )

    # Step 3: Affine Geotransform to GeoJSON Polygons
    t2 = time.perf_counter()
    meta_json = image_row.metadata_json or {}
    transform = meta_json.get("transform", [1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    width, height = image_row.width, image_row.height
    epsg = image_row.epsg

    features = []
    total_area_m2 = 0.0

    for idx, b in enumerate(boxes):
        geojson_poly, area_m2 = transform_box_to_geojson_polygon(
            box=b,
            width=width,
            height=height,
            transform=transform,
            epsg=epsg,
        )
        total_area_m2 += area_m2
        features.append({
            "type": "Feature",
            "id": f"region_{idx + 1}",
            "properties": {
                "label": referring_expression,
                "confidence": raw_confidence,
                "area_m2": area_m2,
                "bbox_normalized": b,
                "bbox_pixel": {
                    "ymin": int(b["ymin"] * height),
                    "xmin": int(b["xmin"] * width),
                    "ymax": int(b["ymax"] * height),
                    "xmax": int(b["xmax"] * width),
                },
            },
            "geometry": geojson_poly,
        })

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    steps.append(
        ExecutionStep(
            step_number=3,
            tool="affine_geotransform_and_area",
            description=f"Transformed {len(features)} box(es) into GeoJSON polygons (Total Ground Area: {total_area_m2:,.1f} m²)",
            status="completed",
            duration_ms=int((time.perf_counter() - t2) * 1000),
            output_summary=f"Area: {total_area_m2:,.1f} m²",
        )
    )

    # Step 4: Resolution & Confidence Evaluation
    t3 = time.perf_counter()
    x_res = 10.0
    y_res = 10.0
    if image_row.resolution and isinstance(image_row.resolution, dict):
        x_res = float(image_row.resolution.get("x_res", 10.0))
        y_res = float(image_row.resolution.get("y_res", 10.0))

    confidence = compute_vqa_confidence(
        model_confidence=raw_confidence,
        x_res=x_res,
        y_res=y_res,
    )

    steps.append(
        ExecutionStep(
            step_number=4,
            tool="evaluate_confidence_and_provenance",
            description=f"Calculated spatial grounding confidence: {int(confidence.overall * 100)}%",
            status="completed",
            duration_ms=int((time.perf_counter() - t3) * 1000),
        )
    )

    # Step 5: Evidence Construction
    claim_text = (
        f"Grounded '{referring_expression}' in {image_row.filename}: "
        f"{len(features)} region(s) identified covering {total_area_m2:,.1f} m²."
    )

    evidence = build_evidence(
        claim=claim_text,
        source_analysis_id=job_id,
        source_image_ids=[image_id],
        model_used="geochat_7b",
        confidence=confidence,
        output_geometry=feature_collection,
        execution_steps=steps,
        artifacts=[image_row.preview_path] if image_row.preview_path else [],
    )

    # Step 6: Save Analysis Job Record
    job = AnalysisJob(
        id=job_id,
        aoi_id=image_row.aoi_id,
        task="visual_grounding",
        status="completed",
        question=f"Locate: {referring_expression}",
        result={
            "referring_expression": referring_expression,
            "feature_collection": feature_collection,
            "total_area_m2": total_area_m2,
            "evidence_id": evidence.id,
        },
        confidence=confidence.overall,
    )
    db.add(job)
    db.commit()

    return {
        "job_id": job_id,
        "image_id": image_id,
        "referring_expression": referring_expression,
        "regions_geojson": feature_collection,
        "total_area_m2": total_area_m2,
        "confidence": confidence.to_dict(),
        "evidence": evidence.to_dict(),
        "execution_steps": [s.to_dict() for s in steps],
        "total_duration_ms": int((time.perf_counter() - start_total_t) * 1000),
    }
