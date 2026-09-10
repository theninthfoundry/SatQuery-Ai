"""Image ingestion, inspection, and preview routes."""

from pathlib import Path
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...db import get_db
from ...models_db import ImageRecord
from ...config import settings
from ...geospatial import (
    extract_raster_metadata,
    validate_file_path,
    validate_raster_metadata,
    ValidationResult,
)
from ...assets import InputSanitizer, AssetFactory, CompatibilityEngine
from ...storage import storage_manager, generate_raster_preview
from ..schemas import (
    ImageInspectionResponse,
    ValidationResultSchema,
    PreviewInfoSchema,
    RasterMetadataSchema,
    CompatibilityCheckRequest,
    CompatibilityReportSchema,
)

router = APIRouter(prefix="/api/v1/images", tags=["images"])


@router.post("/inspect", response_model=ImageInspectionResponse)
async def inspect_image(
    file: UploadFile = File(...),
    aoi_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload and inspect a GeoTIFF or satellite image, extracting metadata, CRS, and generating a preview."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    image_id = storage_manager.generate_image_id()

    try:
        # 1. Save uploaded file safely
        saved_path = storage_manager.save_upload_file(file, image_id)

        # 2. Input sanitization & security checks
        sanitizer = InputSanitizer()
        san_res = sanitizer.sanitize(saved_path, original_filename=file.filename)
        if not san_res.safe:
            return ImageInspectionResponse(
                id=image_id,
                status="invalid",
                metadata=None,
                validation=ValidationResultSchema(
                    valid=False,
                    warnings=san_res.warnings,
                    errors=san_res.errors,
                ),
                preview=PreviewInfoSchema(available=False),
            )

        # 3. Path validation check
        path_validation = validate_file_path(saved_path, max_size_mb=settings.max_upload_size_mb)
        if not path_validation.valid:
            return ImageInspectionResponse(
                id=image_id,
                status="invalid",
                metadata=None,
                validation=ValidationResultSchema(
                    valid=False,
                    warnings=path_validation.warnings + san_res.warnings,
                    errors=path_validation.errors + san_res.errors,
                ),
                preview=PreviewInfoSchema(available=False),
            )

        # 4. Extract comprehensive raster metadata & EarthObservationAsset descriptor
        eo_asset_dict = None
        try:
            eo_asset = AssetFactory.from_file(saved_path, image_id)
            eo_asset_dict = eo_asset.to_dict()
        except Exception as e:
            san_res.warnings.append(f"EOAsset descriptor extraction notice: {str(e)}")

        try:
            metadata = extract_raster_metadata(saved_path)
        except Exception as e:
            return ImageInspectionResponse(
                id=image_id,
                status="error",
                metadata=None,
                validation=ValidationResultSchema(
                    valid=False,
                    warnings=san_res.warnings,
                    errors=[f"Raster parsing failed: {str(e)}"],
                ),
                preview=PreviewInfoSchema(available=False),
            )

        # 5. Validate extracted metadata
        raster_validation = validate_raster_metadata(metadata)
        combined_warnings = path_validation.warnings + raster_validation.warnings + san_res.warnings
        combined_errors = path_validation.errors + raster_validation.errors + san_res.errors

        # 6. Generate Web-compatible preview PNG
        preview_path = storage_manager.get_preview_path(image_id)
        preview_available = False
        try:
            generate_raster_preview(saved_path, preview_path)
            preview_available = preview_path.exists()
        except Exception as e:
            combined_warnings.append(f"Preview generation failed: {str(e)}")

        preview_url = f"/api/v1/images/{image_id}/preview" if preview_available else None

        # 7. Store metadata & asset record in database
        meta_dict = metadata.to_dict()
        if eo_asset_dict:
            meta_dict["asset_descriptor"] = eo_asset_dict

        db_image = ImageRecord(
            id=image_id,
            aoi_id=aoi_id,
            filename=file.filename,
            path=str(saved_path.resolve()),
            preview_path=str(preview_path.resolve()) if preview_available else None,
            format=metadata.format,
            modality=metadata.modality.modality,
            width=metadata.width,
            height=metadata.height,
            band_count=metadata.band_count,
            dtype=metadata.dtype,
            crs=metadata.crs.name,
            epsg=metadata.crs.epsg,
            bounds=metadata.bounds.wgs84 if metadata.bounds else None,
            resolution={
                "x_res": metadata.resolution.x_res,
                "y_res": metadata.resolution.y_res,
                "units": metadata.resolution.units,
            },
            metadata_json=meta_dict,
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        return ImageInspectionResponse(
            id=image_id,
            status="ready" if raster_validation.valid else "invalid",
            metadata=RasterMetadataSchema(**metadata.to_dict()),
            validation=ValidationResultSchema(
                valid=raster_validation.valid,
                warnings=combined_warnings,
                errors=combined_errors,
            ),
            preview=PreviewInfoSchema(
                available=preview_available,
                preview_url=preview_url,
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing image: {str(e)}",
        )


@router.post("/compatibility", response_model=CompatibilityReportSchema)
def check_images_compatibility(
    req: CompatibilityCheckRequest,
    db: Session = Depends(get_db),
):
    """Validate scientific compatibility between two EO assets (spatial overlap, CRS, resolution, modality)."""
    img1 = db.get(ImageRecord, req.image_id_1)
    if not img1:
        raise HTTPException(status_code=404, detail=f"Image 1 not found: {req.image_id_1}")
    img2 = db.get(ImageRecord, req.image_id_2)
    if not img2:
        raise HTTPException(status_code=404, detail=f"Image 2 not found: {req.image_id_2}")

    try:
        asset1 = AssetFactory.from_file(Path(img1.path), img1.id)
        asset2 = AssetFactory.from_file(Path(img2.path), img2.id)

        engine = CompatibilityEngine()
        report = engine.check_compatibility(asset1, asset2, intended_task=req.intended_task or "change_detection")

        return CompatibilityReportSchema(
            compatible=report.compatible,
            overall_score=report.overall_score,
            spatial_overlap=report.spatial_overlap,
            crs_compatible=report.crs_compatible,
            crs_same=report.crs_same,
            resolution_ratio=report.resolution_ratio,
            resolution_compatible=report.resolution_compatible,
            temporal_gap_days=report.temporal_gap_days,
            modality_pair=report.modality_pair,
            warnings=report.warnings,
            errors=report.errors,
            recommendations=report.recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compatibility: {str(e)}",
        )


from pydantic import BaseModel
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.mask import mask as rasterio_mask
import pyproj
from shapely.geometry import shape as shapely_shape
from shapely.ops import transform as shapely_transform


class PixelInspectRequest(BaseModel):
    lat: float
    lon: float
    compare_image_id: Optional[str] = None


class ZonalStatsRequest(BaseModel):
    geometry: dict
    band_index: int = 1


def _sample_pixel(ds: Any, lat: float, lon: float) -> dict:
    """Helper to sample bands and compute spectral indices at a WGS84 point."""
    if ds.crs and ds.crs.to_epsg() != 4326:
        transformer = pyproj.Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
        x_proj, y_proj = transformer.transform(lon, lat)
    else:
        x_proj, y_proj = lon, lat

    row, col = ds.index(x_proj, y_proj)
    if row < 0 or row >= ds.height or col < 0 or col >= ds.width:
        return {
            "in_bounds": False,
            "status": "out_of_bounds",
            "lat": lat,
            "lon": lon,
            "row": row,
            "col": col,
        }

    # Read window
    window = Window(col, row, 1, 1)
    data = ds.read(window=window)[:, 0, 0]

    # Map bands
    band_vals = {}
    band_count = ds.count
    band_names = ["B02", "B03", "B04", "B08", "B11", "B12"] if band_count >= 4 else [f"Band_{i+1}" for i in range(band_count)]
    if band_count == 1:
        band_names = ["VV_or_Intensity"]
    elif band_count == 2:
        band_names = ["VV", "VH"]

    for idx, val in enumerate(data):
        b_name = band_names[idx] if idx < len(band_names) else f"Band_{idx+1}"
        # Normalize 16-bit DN if in [0, 10000] scale
        raw_val = float(val)
        norm_val = round(raw_val / 10000.0, 4) if raw_val > 1.0 and raw_val <= 10000 else round(raw_val, 4)
        band_vals[b_name] = norm_val

    # Compute indices
    indices = {}
    if band_count >= 4:
        # standard 4-band Blue, Green, Red, NIR
        b_blue = float(data[0])
        b_green = float(data[1])
        b_red = float(data[2])
        b_nir = float(data[3])

        # NDVI
        denom_ndvi = b_nir + b_red
        if denom_ndvi != 0:
            indices["NDVI"] = round(float((b_nir - b_red) / denom_ndvi), 4)

        # NDWI
        denom_ndwi = b_green + b_nir
        if denom_ndwi != 0:
            indices["NDWI"] = round(float((b_green - b_nir) / denom_ndwi), 4)

        if band_count >= 5:
            b_swir = float(data[4])
            denom_ndbi = b_swir + b_nir
            if denom_ndbi != 0:
                indices["NDBI"] = round(float((b_swir - b_nir) / denom_ndbi), 4)

    elif band_count in (1, 2):
        # SAR
        vv_val = float(data[0])
        indices["Sigma0_VV_dB"] = round(10.0 * float(np.log10(max(vv_val, 1e-8))), 2)
        if band_count >= 2:
            vh_val = float(data[1])
            indices["Sigma0_VH_dB"] = round(10.0 * float(np.log10(max(vh_val, 1e-8))), 2)

    is_nodata = False
    if ds.nodata is not None:
        is_nodata = any(val == ds.nodata for val in data)

    res_x = abs(ds.res[0])
    # If degree, approximate to meters (~111,320m per degree)
    gsd_m = round(res_x * 111320.0, 2) if res_x < 0.01 else round(res_x, 2)

    return {
        "in_bounds": True,
        "status": "ok",
        "lat": lat,
        "lon": lon,
        "row": row,
        "col": col,
        "crs": ds.crs.to_string() if ds.crs else "EPSG:4326",
        "gsd_meters": gsd_m,
        "nodata": is_nodata,
        "bands": band_vals,
        "indices": indices,
    }


@router.get("/timeline")
def get_images_timeline(db: Session = Depends(get_db)):
    """Retrieve multi-epoch observatory timeline of all registered scenes (4-12 observations)."""
    images = db.query(ImageRecord).order_by(ImageRecord.created_at.asc()).all()
    timeline = []
    for img in images:
        meta = img.metadata_json or {}
        asset_desc = meta.get("asset_descriptor")
        asset_desc = asset_desc if isinstance(asset_desc, dict) else {}
        sensor_info = asset_desc.get("sensor")
        sensor_info = sensor_info if isinstance(sensor_info, dict) else {}
        platform_name = sensor_info.get("platform") or ("Sentinel-2" if img.modality == "multispectral" else "Sentinel-1")

        timeline.append({
            "id": img.id,
            "filename": img.filename,
            "date": img.created_at.strftime("%Y-%m-%d") if img.created_at else None,
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "modality": img.modality,
            "platform": platform_name,
            "cloud_cover_percentage": meta.get("cloud_cover_percentage", 0.0),
            "resolution_m": img.resolution.get("x_res", 10.0) if isinstance(img.resolution, dict) else 10.0,
            "crs": img.crs,
            "bounds": img.bounds,
            "preview_url": f"/api/v1/images/{img.id}/preview" if img.preview_path else None,
        })
    return {"count": len(timeline), "timeline": timeline}


@router.post("/{image_id}/pixel-inspect")
def inspect_image_pixel(
    image_id: str,
    payload: PixelInspectRequest,
    db: Session = Depends(get_db),
):
    """Microscope-level pixel inspection extracting band values, indices, and T1 vs T2 deltas."""
    img = db.get(ImageRecord, image_id)
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

    p = Path(img.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Image raster file not found on disk: {img.path}")

    try:
        with rasterio.open(str(p)) as ds:
            result = _sample_pixel(ds, payload.lat, payload.lon)
            result["image_id"] = image_id
            result["filename"] = img.filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Raster pixel sampling error: {str(e)}")

    # If comparison image requested, sample T2 at the same coordinate
    if payload.compare_image_id:
        img2 = db.get(ImageRecord, payload.compare_image_id)
        if img2 and Path(img2.path).exists():
            try:
                with rasterio.open(str(img2.path)) as ds2:
                    t2_res = _sample_pixel(ds2, payload.lat, payload.lon)
                    t2_res["image_id"] = payload.compare_image_id
                    t2_res["filename"] = img2.filename

                    comparison = {
                        "t1_image_id": image_id,
                        "t2_image_id": payload.compare_image_id,
                        "t1_indices": result.get("indices", {}),
                        "t2_indices": t2_res.get("indices", {}),
                        "delta_indices": {},
                    }
                    for k, v in t2_res.get("indices", {}).items():
                        if k in result.get("indices", {}):
                            comparison["delta_indices"][k] = round(v - result["indices"][k], 4)

                    result["comparison"] = comparison
            except Exception as e:
                result["comparison_error"] = str(e)

    return result


@router.post("/{image_id}/zonal-stats")
def compute_zonal_stats(
    image_id: str,
    payload: ZonalStatsRequest,
    db: Session = Depends(get_db),
):
    """Compute deterministic zonal statistics (count, mean, median, std, min, max, percentiles) for a polygon AOI."""
    img = db.get(ImageRecord, image_id)
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

    p = Path(img.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Image raster file not found on disk: {img.path}")

    try:
        poly_geom = shapely_shape(payload.geometry)
        with rasterio.open(str(p)) as ds:
            # Reproject geometry to dataset CRS if needed
            if ds.crs and ds.crs.to_epsg() != 4326:
                transformer = pyproj.Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
                poly_proj = shapely_transform(transformer.transform, poly_geom)
            else:
                poly_proj = poly_geom

            band_idx = min(max(1, payload.band_index), ds.count)
            masked_data, _ = rasterio_mask(ds, [poly_proj], crop=True, indexes=band_idx)

            # Masked data shape: (1, H, W)
            arr = masked_data[0].astype(np.float64)
            valid_mask = np.isfinite(arr)
            if ds.nodata is not None:
                valid_mask &= (arr != ds.nodata)
            # Filter zero nodata if outside boundary
            valid_pixels = arr[valid_mask]

            if valid_pixels.size == 0:
                return {
                    "image_id": image_id,
                    "band_index": band_idx,
                    "count": 0,
                    "status": "no_valid_pixels",
                }

            return {
                "image_id": image_id,
                "band_index": band_idx,
                "count": int(valid_pixels.size),
                "min": round(float(np.min(valid_pixels)), 4),
                "max": round(float(np.max(valid_pixels)), 4),
                "mean": round(float(np.mean(valid_pixels)), 4),
                "median": round(float(np.median(valid_pixels)), 4),
                "std": round(float(np.std(valid_pixels)), 4),
                "p25": round(float(np.percentile(valid_pixels, 25)), 4),
                "p75": round(float(np.percentile(valid_pixels, 75)), 4),
                "p95": round(float(np.percentile(valid_pixels, 95)), 4),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zonal statistics computation error: {str(e)}")


@router.get("/{image_id}/preview")
def get_image_preview(image_id: str):
    """Serve the generated web preview PNG for a given image ID."""
    preview_path = storage_manager.get_preview_path(image_id)
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview image not found")
    return FileResponse(preview_path, media_type="image/png")


@router.get("/{image_id}")
def get_image_metadata(image_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata record for an image."""
    db_image = db.get(ImageRecord, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "id": db_image.id,
        "filename": db_image.filename,
        "format": db_image.format,
        "modality": db_image.modality,
        "width": db_image.width,
        "height": db_image.height,
        "band_count": db_image.band_count,
        "dtype": db_image.dtype,
        "crs": db_image.crs,
        "epsg": db_image.epsg,
        "bounds": db_image.bounds,
        "resolution": db_image.resolution,
        "metadata": db_image.metadata_json,
        "created_at": db_image.created_at,
    }


@router.get("")
def list_images(db: Session = Depends(get_db)):
    """List all ingested images."""
    images = db.query(ImageRecord).order_by(ImageRecord.created_at.desc()).limit(50).all()
    return [
        {
            "id": img.id,
            "filename": img.filename,
            "format": img.format,
            "modality": img.modality,
            "width": img.width,
            "height": img.height,
            "band_count": img.band_count,
            "crs": img.crs,
            "preview_url": f"/api/v1/images/{img.id}/preview" if img.preview_path else None,
            "created_at": img.created_at,
        }
        for img in images
    ]
