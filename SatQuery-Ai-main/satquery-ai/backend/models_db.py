"""SQLAlchemy database models for SatQuery AI."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base


def gen_uuid():
    return str(uuid.uuid4())


class AOI(Base):
    __tablename__ = "aois"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    geometry = Column(JSON, nullable=True)  # GeoJSON Polygon / MultiPolygon
    geometry_geojson = Column(JSON, nullable=True)
    area_ha = Column(Float, nullable=True)
    perimeter_m = Column(Float, nullable=True)
    bbox = Column(JSON, nullable=True)
    crs = Column(String, default="EPSG:4326")
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("ImageRecord", back_populates="aoi", cascade="all, delete-orphan")


AOIRecord = AOI


class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, default=lambda: f"img_{uuid.uuid4().hex[:12]}")
    aoi_id = Column(String, ForeignKey("aois.id"), nullable=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    preview_path = Column(String, nullable=True)
    format = Column(String, nullable=False, default="GeoTIFF")
    modality = Column(String, default="unknown")
    acquisition_date = Column(DateTime, nullable=True)
    width = Column(Integer, default=256, nullable=False)
    height = Column(Integer, default=256, nullable=False)
    band_count = Column(Integer, default=3, nullable=False)
    dtype = Column(String, default="uint8", nullable=False)
    crs = Column(String, nullable=True)
    epsg = Column(Integer, nullable=True)
    bounds = Column(JSON, nullable=True)
    resolution = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    aoi = relationship("AOI", back_populates="images")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    aoi_id = Column(String, ForeignKey("aois.id"), nullable=True)
    task = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    question = Column(String, nullable=True)
    query = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)
    confidence = Column(JSON, nullable=True)
    confidence_json = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        # Normalize synonyms
        if "query" in kwargs and "question" not in kwargs:
            kwargs["question"] = kwargs["query"]
        elif "question" in kwargs and "query" not in kwargs:
            kwargs["query"] = kwargs["question"]

        if "result_json" in kwargs and "result" not in kwargs:
            kwargs["result"] = kwargs["result_json"]
        elif "result" in kwargs and "result_json" not in kwargs:
            kwargs["result_json"] = kwargs["result"]

        if "confidence_json" in kwargs and "confidence" not in kwargs:
            kwargs["confidence"] = kwargs["confidence_json"]
        elif "confidence" in kwargs and "confidence_json" not in kwargs:
            kwargs["confidence_json"] = kwargs["confidence"]

        super().__init__(**kwargs)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False)
    source_image_id = Column(String, ForeignKey("images.id"), nullable=True)
    model_used = Column(String, nullable=False)
    output_geometry = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
