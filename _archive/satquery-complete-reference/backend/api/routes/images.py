"""
backend/api/routes/images.py

Input upload and compatibility checking, as required by the "Expected
Solution" section: accepts GeoTIFF/TIFF (and PNG/JPEG for benchmark
datasets), validates it can be opened and has usable spatial metadata,
and returns the info the frontend needs to render the layer + let the
user pick a modality (optical/SAR) for pairing.
"""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.config.settings import REPO_ROOT
from backend.geospatial import engine as geo

router = APIRouter()
UPLOAD_DIR = REPO_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported extension {ext}. Allowed: {sorted(ALLOWED_EXT)}")

    image_id = uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{image_id}{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    response = {"image_id": image_id, "path": str(dest), "filename": file.filename}

    if ext in (".tif", ".tiff"):
        try:
            info = geo.read_raster_info(str(dest))
            response.update({
                "width": info.width, "height": info.height, "bands": info.count,
                "crs_epsg": info.crs_epsg, "gsd_x": info.gsd_x, "gsd_y": info.gsd_y,
                "has_geospatial_metadata": info.crs_epsg is not None,
                "bounds": info.bounds_geo,
            })
        except Exception as e:
            dest.unlink(missing_ok=True)
            raise HTTPException(422, f"Could not read GeoTIFF metadata: {e}")
    else:
        response.update({
            "has_geospatial_metadata": False,
            "note": "PNG/JPEG accepted for benchmark datasets only -- no geodetic outputs "
                    "(area/coordinates) will be produced for this input.",
        })

    return response


@router.get("/{image_id}")
async def get_image_info(image_id: str):
    matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not matches:
        raise HTTPException(404, "image_id not found")
    path = matches[0]
    if path.suffix.lower() in (".tif", ".tiff"):
        info = geo.read_raster_info(str(path))
        return {"image_id": image_id, "path": str(path), **info.__dict__}
    return {"image_id": image_id, "path": str(path)}
