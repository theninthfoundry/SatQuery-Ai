"""Area of Interest (AOI) management routes."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...models_db import AOI

router = APIRouter(prefix="/api/v1/aoi", tags=["aoi"])


class AOICreateSchema(BaseModel):
    name: str
    geometry: Dict[str, Any]


@router.post("")
def create_aoi(payload: AOICreateSchema, db: Session = Depends(get_db)):
    """Create a new Area of Interest (AOI)."""
    aoi = AOI(name=payload.name, geometry=payload.geometry)
    db.add(aoi)
    db.commit()
    db.refresh(aoi)
    return {"id": aoi.id, "name": aoi.name, "geometry": aoi.geometry, "created_at": aoi.created_at}


@router.get("/{aoi_id}")
def get_aoi(aoi_id: str, db: Session = Depends(get_db)):
    """Retrieve an AOI by ID."""
    aoi = db.get(AOI, aoi_id)
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")
    return {"id": aoi.id, "name": aoi.name, "geometry": aoi.geometry, "created_at": aoi.created_at}


@router.get("")
def list_aois(db: Session = Depends(get_db)):
    """List all registered AOIs."""
    aois = db.query(AOI).order_by(AOI.created_at.desc()).all()
    return [{"id": a.id, "name": a.name, "geometry": a.geometry, "created_at": a.created_at} for a in aois]
