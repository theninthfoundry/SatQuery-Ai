"""Health check endpoints for SatQuery AI."""

from fastapi import APIRouter
from ...config import settings
from ...models.manager import gpu_manager
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def root_health():
    """Basic service health check."""
    return HealthResponse(
        status="ok",
        service="satquery-api",
    )


@router.get("/api/v1/health", response_model=HealthResponse)
def api_v1_health():
    """Detailed health check including version, environment, and hardware status."""
    return HealthResponse(
        status="ok",
        service="satquery-api",
        version="0.1.0",
        environment=settings.app_env,
        hardware=gpu_manager.get_hardware_status(),
    )
