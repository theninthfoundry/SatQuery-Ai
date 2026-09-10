"""Model registry and GPU management API routes."""

from fastapi import APIRouter
from ...models.registry import model_registry
from ...models.manager import gpu_manager

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("")
def list_models():
    """List all registered AI models, tasks, and availability status with honest truth states."""
    import json
    from pathlib import Path
    manifest_path = Path(__file__).resolve().parent.parent.parent.parent / "models_manifest.json"
    manifest_data = None
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            pass

    return {
        "models": model_registry.list_models(),
        "manifest": manifest_data,
        "hardware": gpu_manager.get_hardware_status(),
    }


@router.get("/{model_key}/health")
def model_health(model_key: str):
    """Inspect the status and health of a specific model adapter."""
    adapter = model_registry.get(model_key)
    if not adapter:
        return {"status": "not_found", "model": model_key}
    return adapter.health()
