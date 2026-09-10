"""
backend/api/main.py

FastAPI entrypoint. Run with:
    uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import analysis, images, reports, system

app = FastAPI(
    title="SatQuery AI",
    description="Agentic vision-language assistant for multimodal remote-sensing analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/")
def root():
    return {"service": "SatQuery AI", "status": "ready", "docs": "/docs"}
