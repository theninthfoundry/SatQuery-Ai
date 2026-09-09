"""Area of Interest (AOI) management and ingestion routes."""

import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from shapely.geometry import shape

from ...db import get_db
from ...models_db import AOI, ImageRecord
from ...geospatial.aoi_importer import import_aoi_file, _repair_and_finalize_geometry

router = APIRouter(prefix="/api/v1/aoi", tags=["aoi"])


class AOICreateSchema(BaseModel):
    name: str
    geometry: Dict[str, Any]
    description: Optional[str] = None


def _serialize_aoi(aoi: AOI) -> Dict[str, Any]:
    area_m2 = round(aoi.area_ha * 10000.0, 2) if aoi.area_ha is not None else None
    return {
        "id": aoi.id,
        "name": aoi.name,
        "description": aoi.description,
        "geometry": aoi.geometry,
        "area_ha": aoi.area_ha,
        "area_m2": area_m2,
        "perimeter_m": aoi.perimeter_m,
        "bbox": aoi.bbox,
        "crs": aoi.crs or "EPSG:4326",
        "created_at": aoi.created_at.isoformat() if aoi.created_at else None,
    }


@router.post("")
def create_aoi(payload: AOICreateSchema, db: Session = Depends(get_db)):
    """Create a new Area of Interest (AOI) with validated geometry and computed geodesic metrics."""
    try:
        s_geom = shape(payload.geometry)
        final_geom, bbox, area_m2, area_ha, perimeter_m, _ = _repair_and_finalize_geometry(s_geom, "EPSG:4326")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid polygonal geometry: {str(e)}",
        )

    aoi = AOI(
        name=payload.name,
        description=payload.description,
        geometry=payload.geometry,
        geometry_geojson=payload.geometry,
        area_ha=area_ha,
        perimeter_m=perimeter_m,
        bbox=bbox,
        crs="EPSG:4326",
    )
    db.add(aoi)
    db.commit()
    db.refresh(aoi)
    return _serialize_aoi(aoi)


@router.post("/upload")
async def upload_aoi(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload and parse an AOI file (GeoJSON, KML, KMZ, or Shapefile ZIP).
    
    Performs security sanitization against Zip Slip, repairs topological errors,
    reprojects to EPSG:4326, and calculates deterministic geodesic area/perimeter.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    aoi_name = name or file.filename.rsplit(".", 1)[0]
    parse_result = import_aoi_file(content, file.filename, custom_name=aoi_name)

    if not parse_result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Failed to parse AOI file",
                "errors": parse_result.errors,
                "warnings": parse_result.warnings,
            },
        )

    aoi = AOI(
        name=parse_result.name,
        description=f"Imported from {file.filename}",
        geometry=parse_result.geometry,
        geometry_geojson=parse_result.geometry,
        area_ha=parse_result.area_ha,
        perimeter_m=parse_result.perimeter_m,
        bbox=parse_result.bbox,
        crs=parse_result.crs,
    )
    db.add(aoi)
    db.commit()
    db.refresh(aoi)

    res = _serialize_aoi(aoi)
    res["warnings"] = parse_result.warnings
    return res


@router.get("/{aoi_id}")
def get_aoi(aoi_id: str, db: Session = Depends(get_db)):
    """Retrieve an AOI by ID."""
    aoi = db.get(AOI, aoi_id)
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")
    return _serialize_aoi(aoi)


@router.get("/{aoi_id}/observations")
def get_aoi_observations(aoi_id: str, db: Session = Depends(get_db)):
    """Retrieve multi-temporal observation history associated with or intersecting this AOI."""
    aoi = db.get(AOI, aoi_id)
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")

    images = db.query(ImageRecord).filter(
        (ImageRecord.aoi_id == aoi_id) | (ImageRecord.is_valid == True)
    ).order_by(ImageRecord.created_at.desc()).all()

    observations = []
    for img in images:
        meta = img.metadata_json or {}
        asset_desc = meta.get("asset_descriptor")
        asset_desc = asset_desc if isinstance(asset_desc, dict) else {}
        sensor_info = asset_desc.get("sensor")
        sensor_info = sensor_info if isinstance(sensor_info, dict) else {}
        platform_name = sensor_info.get("platform") or ("Sentinel-2" if img.modality == "multispectral" else "Sentinel-1")

        observations.append({
            "id": img.id,
            "filename": img.filename,
            "date": img.created_at.strftime("%Y-%m-%d") if img.created_at else None,
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "modality": img.modality,
            "sensor": sensor_info.get("sensor", img.modality),
            "platform": platform_name,
            "cloud_cover_percentage": meta.get("cloud_cover_percentage", 0.0),
            "resolution_m": img.resolution.get("x_res", 10.0) if isinstance(img.resolution, dict) else 10.0,
            "bounds": img.bounds,
            "preview_url": f"/api/v1/images/{img.id}/preview" if img.preview_path else None,
        })

    return {
        "aoi": _serialize_aoi(aoi),
        "observation_count": len(observations),
        "observations": observations,
    }


@router.get("")
def list_aois(db: Session = Depends(get_db)):
    """List all registered AOIs with their bounding boxes and area metrics."""
    aois = db.query(AOI).order_by(AOI.created_at.desc()).all()
    return [_serialize_aoi(a) for a in aois]
