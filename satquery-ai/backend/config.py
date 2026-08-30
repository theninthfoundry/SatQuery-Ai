"""SatQuery AI — Application Configuration.

Robust multi-mode configuration supporting pydantic-settings, standard pydantic,
or pure Python standard library environment fallbacks.
"""

import os
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
    HAS_PYDANTIC_SETTINGS = True
except ImportError:
    HAS_PYDANTIC_SETTINGS = False

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


if HAS_PYDANTIC_SETTINGS:
    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

        app_env: str = Field(default="development", validation_alias="APP_ENV")
        debug: bool = Field(default=True, validation_alias="DEBUG")
        api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
        api_port: int = Field(default=8000, validation_alias="API_PORT")

        # Database
        database_url: str = Field(
            default="sqlite:///./satquery.db",
            validation_alias="DATABASE_URL",
        )

        # File Storage
        data_dir: Path = Field(default=Path("./data"), validation_alias="DATA_DIR")
        max_upload_size_mb: int = Field(default=512, validation_alias="MAX_UPLOAD_SIZE_MB")

        # Hardware & Model Cache
        model_cache_dir: Path = Field(default=Path("./checkpoints"), validation_alias="MODEL_CACHE_DIR")
        cuda_visible_devices: str = Field(default="0", validation_alias="CUDA_VISIBLE_DEVICES")
        force_cpu: bool = Field(default=False, validation_alias="FORCE_CPU")

        # CORS
        cors_origins: List[str] = Field(
            default=["http://localhost:3000", "http://127.0.0.1:3000"],
            validation_alias="CORS_ORIGINS",
        )

        @property
        def upload_dir(self) -> Path:
            path = self.data_dir / "uploads"
            path.mkdir(parents=True, exist_ok=True)
            return path

        @property
        def preview_dir(self) -> Path:
            path = self.data_dir / "previews"
            path.mkdir(parents=True, exist_ok=True)
            return path

        @property
        def checkpoint_dir(self) -> Path:
            self.model_cache_dir.mkdir(parents=True, exist_ok=True)
            return self.model_cache_dir

    settings = Settings()

else:
    # Pure Python / Standard Library Fallback Settings
    class PureSettings:
        def __init__(self):
            self.app_env: str = os.getenv("APP_ENV", "development")
            self.debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1")
            self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
            self.api_port: int = int(os.getenv("API_PORT", "8000"))
            self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./satquery.db")
            self.data_dir: Path = Path(os.getenv("DATA_DIR", "./data"))
            self.max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "512"))
            self.model_cache_dir: Path = Path(os.getenv("MODEL_CACHE_DIR", "./checkpoints"))
            self.cuda_visible_devices: str = os.getenv("CUDA_VISIBLE_DEVICES", "0")
            self.force_cpu: bool = os.getenv("FORCE_CPU", "false").lower() in ("true", "1")
            self.cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

        @property
        def upload_dir(self) -> Path:
            path = self.data_dir / "uploads"
            path.mkdir(parents=True, exist_ok=True)
            return path

        @property
        def preview_dir(self) -> Path:
            path = self.data_dir / "previews"
            path.mkdir(parents=True, exist_ok=True)
            return path

        @property
        def checkpoint_dir(self) -> Path:
            self.model_cache_dir.mkdir(parents=True, exist_ok=True)
            return self.model_cache_dir

    settings = PureSettings()
