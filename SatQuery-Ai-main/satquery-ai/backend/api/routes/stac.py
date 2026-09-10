"""STAC catalog discovery and scene search endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...ingestion.stac_client import STACClient

router = APIRouter(prefix="/api/v1/stac", tags=["stac"])
stac_client = STACClient()


class STACSearchRequest(BaseModel):
    bbox: List[float] = Field(default=[78.40, 17.30, 78.55, 17.45], description="[min_lon, min_lat, max_lon, max_lat]")
    start_date: str = Field(default="2024-01-01")
    end_date: str = Field(default="2026-12-31")
    collection: str = Field(default="sentinel-2-l2a")
    max_cloud_cover: float = Field(default=20.0, ge=0.0, le=100.0)
    limit: int = Field(default=10, ge=1, le=50)


@router.post("/search")
def search_stac_scenes(payload: STACSearchRequest):
    """Search for Sentinel-1 / Sentinel-2 satellite scenes via STAC."""
    try:
        items, is_live, msg = stac_client.search(
            bbox=payload.bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            collection=payload.collection,
            max_cloud_cover=payload.max_cloud_cover,
            limit=payload.limit,
        )
        return {
            "online": is_live,
            "status_message": msg,
            "count": len(items),
            "collection": payload.collection,
            "items": [item.to_dict() for item in items],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STAC search failed: {str(e)}")
