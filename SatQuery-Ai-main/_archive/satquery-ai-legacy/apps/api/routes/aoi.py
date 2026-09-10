from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AOI
from ..schemas import AOICreateRequest, AOICreateResponse

router = APIRouter()


@router.post("/aoi", response_model=AOICreateResponse)
def create_aoi(req: AOICreateRequest, db: Session = Depends(get_db)):
    aoi = AOI(name=req.name, geometry=req.geometry)
    db.add(aoi)
    db.commit()
    db.refresh(aoi)
    return AOICreateResponse(aoi_id=aoi.id)
