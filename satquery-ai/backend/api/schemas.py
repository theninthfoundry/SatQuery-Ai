"""Pydantic schemas for SatQuery API."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CRSInfoSchema(BaseModel):
    present: bool
    valid: bool
    epsg: Optional[int] = None
    name: Optional[str] = None
    type: str  # "projected", "geographic", "compound", "unknown", "missing"
    status: str  # "ok", "warning", "missing"
    units: Optional[str] = None


class BoundingBoxSchema(BaseModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    wgs84: Optional[Dict[str, float]] = None


class SpatialResolutionSchema(BaseModel):
    x_res: float
    y_res: float
    units: str


class BandStatisticsSchema(BaseModel):
    band_index: int
    dtype: str
    min: float
    max: float
    mean: float
    std: Optional[float] = None
    nodata: Optional[float] = None


class ModalitySchema(BaseModel):
    detected: str
    confidence: float
    basis: List[str] = []


class RasterMetadataSchema(BaseModel):
    filename: str
    format: str
    driver: Optional[str] = None
    width: int
    height: int
    band_count: int
    dtype: str
    crs: CRSInfoSchema
    transform: List[float]
    bounds: Optional[BoundingBoxSchema] = None
    resolution: SpatialResolutionSchema
    nodata: Optional[float] = None
    compression: Optional[str] = None
    bands: List[BandStatisticsSchema] = []
    modality: ModalitySchema
    tags: Dict[str, str] = {}


class ValidationResultSchema(BaseModel):
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


class PreviewInfoSchema(BaseModel):
    available: bool
    preview_url: Optional[str] = None


class ImageInspectionResponse(BaseModel):
    id: str
    status: str  # "ready", "invalid", "error"
    metadata: Optional[RasterMetadataSchema] = None
    validation: ValidationResultSchema
    preview: PreviewInfoSchema


class HealthResponse(BaseModel):
    status: str
    service: str
    version: Optional[str] = None
    environment: Optional[str] = None
    hardware: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    question: str
    aoi_id: Optional[str] = None
    image_id: Optional[str] = None
    image_before_id: Optional[str] = None
    image_after_id: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    tool_called: str
    result: Dict[str, Any]
