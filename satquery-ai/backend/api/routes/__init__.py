"""API routes package."""

from .health import router as health_router
from .images import router as images_router
from .models import router as models_router
from .query import router as query_router
from .aoi import router as aoi_router
from .analysis import router as analysis_router
from .evidence import router as evidence_router
from .reports import router as reports_router
from .evaluation import router as evaluation_router

__all__ = [
    "health_router",
    "images_router",
    "models_router",
    "query_router",
    "aoi_router",
    "analysis_router",
    "evidence_router",
    "reports_router",
    "evaluation_router",
]
