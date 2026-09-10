from fastapi import FastAPI

from .db import engine
from .models import Base
from .routes import analysis, aoi, evidence, images, query, report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SatQuery AI", version="0.1.0")

app.include_router(query.router, tags=["query"])
app.include_router(aoi.router, tags=["aoi"])
app.include_router(images.router, tags=["images"])
app.include_router(evidence.router, tags=["evidence"])
app.include_router(analysis.router, tags=["analysis"])
app.include_router(report.router, tags=["report"])


@app.get("/health")
def health():
    return {"status": "ok"}
