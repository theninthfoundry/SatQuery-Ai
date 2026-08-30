from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Image

router = APIRouter()


class ImageCreateRequest(BaseModel):
    aoi_id: str
    sensor: str  # 'optical' | 'sar'
    acquisition_date: datetime
    path: str
    crs: Optional[str] = None


class ImageCreateResponse(BaseModel):
    image_id: str


@router.post("/images", response_model=ImageCreateResponse)
def create_image(req: ImageCreateRequest, db: Session = Depends(get_db)):
    image = Image(
        aoi_id=req.aoi_id,
        sensor=req.sensor,
        acquisition_date=req.acquisition_date,
        path=req.path,
        crs=req.crs,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return ImageCreateResponse(image_id=image.id)
