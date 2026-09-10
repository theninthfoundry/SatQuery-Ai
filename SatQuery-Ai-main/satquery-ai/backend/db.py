"""Database configuration and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# SQLite connection args for multi-threaded FastAPI
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _sqlite_on_connect(dbapi_con, con_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_con.cursor()
        try:
            cursor.execute("PRAGMA table_info(images)")
            columns = [row[1] for row in cursor.fetchall()]
            if columns and "is_valid" not in columns:
                cursor.execute("ALTER TABLE images ADD COLUMN is_valid BOOLEAN DEFAULT 1")
                dbapi_con.commit()

            cursor.execute("PRAGMA table_info(aois)")
            aoi_cols = [row[1] for row in cursor.fetchall()]
            if aoi_cols:
                if "area_ha" not in aoi_cols:
                    cursor.execute("ALTER TABLE aois ADD COLUMN area_ha FLOAT")
                if "perimeter_m" not in aoi_cols:
                    cursor.execute("ALTER TABLE aois ADD COLUMN perimeter_m FLOAT")
                if "bbox" not in aoi_cols:
                    cursor.execute("ALTER TABLE aois ADD COLUMN bbox JSON")
                if "crs" not in aoi_cols:
                    cursor.execute("ALTER TABLE aois ADD COLUMN crs VARCHAR DEFAULT 'EPSG:4326'")
                dbapi_con.commit()

            cursor.execute("PRAGMA table_info(analysis_jobs)")
            job_cols = [row[1] for row in cursor.fetchall()]
            if job_cols:
                if "query" not in job_cols:
                    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN query VARCHAR")
                if "result_json" not in job_cols:
                    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN result_json JSON")
                if "confidence_json" not in job_cols:
                    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN confidence_json JSON")
                if "execution_time_ms" not in job_cols:
                    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN execution_time_ms INTEGER")
                dbapi_con.commit()
        except Exception:
            pass
        finally:
            cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .models_db import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)

