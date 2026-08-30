"""Safe file storage manager with path-traversal prevention."""

import re
import uuid
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
from fastapi import UploadFile

from ..config import settings


class StorageManager:
    """Manages file storage safely, preventing path traversal attacks and organizing uploads/previews."""

    def __init__(self, base_data_dir: Optional[Path] = None):
        self.base_dir = (base_data_dir or settings.data_dir).resolve()
        self.upload_dir = (self.base_dir / "uploads").resolve()
        self.preview_dir = (self.base_dir / "previews").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)

    def generate_image_id(self) -> str:
        """Generate a unique, safe identifier for an image asset."""
        return f"img_{uuid.uuid4().hex[:12]}"

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by stripping directory separators and unsafe characters."""
        # Strip paths
        base_name = Path(filename).name
        # Remove any non-alphanumeric chars except dots, underscores, dashes
        clean_name = re.sub(r"[^\w\.-]", "_", base_name)
        if not clean_name or clean_name.startswith("."):
            clean_name = f"image_{clean_name}"
        return clean_name

    def get_upload_path(self, image_id: str, filename: str) -> Path:
        """Get safe target path for an uploaded image."""
        safe_fn = self.sanitize_filename(filename)
        dest_filename = f"{image_id}_{safe_fn}"
        target_path = (self.upload_dir / dest_filename).resolve()

        # Path traversal guard: must be strictly inside upload_dir
        if not target_path.is_relative_to(self.upload_dir):
            raise ValueError(f"Path traversal detected: {filename}")

        return target_path

    def get_preview_path(self, image_id: str) -> Path:
        """Get safe target path for a preview PNG."""
        target_path = (self.preview_dir / f"{image_id}_preview.png").resolve()
        if not target_path.is_relative_to(self.preview_dir):
            raise ValueError(f"Path traversal detected for preview ID: {image_id}")
        return target_path

    def save_upload_file(self, upload_file: UploadFile, image_id: str) -> Path:
        """Save a FastAPI UploadFile stream safely to disk."""
        target_path = self.get_upload_path(image_id, upload_file.filename or "image.tif")
        with open(target_path, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
        return target_path

    def save_bytes(self, data: bytes, image_id: str, filename: str) -> Path:
        """Save raw bytes safely to disk."""
        target_path = self.get_upload_path(image_id, filename)
        with open(target_path, "wb") as f:
            f.write(data)
        return target_path

    def find_image_path(self, image_id: str) -> Optional[Path]:
        """Find the stored image file given an image ID."""
        for p in self.upload_dir.glob(f"{image_id}_*"):
            if p.is_file():
                return p
        return None


storage_manager = StorageManager()
