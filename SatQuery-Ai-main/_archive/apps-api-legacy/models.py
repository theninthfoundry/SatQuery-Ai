from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def gen_id() -> str:
    return str(uuid.uuid4())


class AOI(Base):
    __tablename__ = "aoi"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    geometry = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Image(Base):
    __tablename__ = "images"
    id = Column(String, primary_key=True, default=gen_id)
    aoi_id = Column(String, ForeignKey("aoi.id"))
    sensor = Column(String, nullable=False)  # 'optical' | 'sar'
    acquisition_date = Column(DateTime, nullable=False)
    path = Column(String, nullable=False)
    crs = Column(String, nullable=True)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id = Column(String, primary_key=True, default=gen_id)
    aoi_id = Column(String, ForeignKey("aoi.id"))
    tool = Column(String, nullable=False)
    status = Column(String, default="pending")
    result_ref = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChangeRegion(Base):
    __tablename__ = "changes"
    id = Column(String, primary_key=True, default=gen_id)
    job_id = Column(String, ForeignKey("analysis_jobs.id"))
    geometry = Column(JSON, nullable=False)
    change_type = Column(String, nullable=True)
    area_m2 = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True, default=gen_id)
    claim = Column(String, nullable=False)
    derived_from_json = Column(JSON, nullable=False)
    confidence_breakdown_json = Column(JSON, nullable=False)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=gen_id)
    aoi_id = Column(String, ForeignKey("aoi.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=True)
