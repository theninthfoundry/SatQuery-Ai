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
    geometry = Column(JSON, nullable=False)  # GeoJSON Polygon / MultiPolygon
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("ImageRecord", back_populates="aoi", cascade="all, delete-orphan")


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
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    band_count = Column(Integer, nullable=False)
    dtype = Column(String, nullable=False)
    crs = Column(String, nullable=True)
    epsg = Column(Integer, nullable=True)
    bounds = Column(JSON, nullable=True)
    resolution = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    aoi = relationship("AOI", back_populates="images")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    aoi_id = Column(String, ForeignKey("aois.id"), nullable=True)
    task = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    question = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False)
    source_image_id = Column(String, ForeignKey("images.id"), nullable=True)
    model_used = Column(String, nullable=False)
    output_geometry = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
