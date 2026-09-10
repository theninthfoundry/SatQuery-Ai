import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Defaults to a local SQLite file so the API runs with zero setup.
# Point DATABASE_URL at the docker-compose Postgres/PostGIS instance
# (see .env.example) once you're past the pure-skeleton stage.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./satquery.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
