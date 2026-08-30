"""SatQuery AI — Main FastAPI Application Entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import engine, Base
from .api.routes import (
    health_router,
    images_router,
    models_router,
    query_router,
    aoi_router,
    analysis_router,
    evidence_router,
    reports_router,
    evaluation_router,
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SatQuery AI API",
    description="Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router)
app.include_router(images_router)
app.include_router(models_router)
app.include_router(query_router)
app.include_router(aoi_router)
app.include_router(analysis_router)
app.include_router(evidence_router)
app.include_router(reports_router)
app.include_router(evaluation_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
