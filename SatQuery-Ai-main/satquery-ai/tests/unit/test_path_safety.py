"""Unit tests for storage manager path safety and path traversal protection."""

import pytest
from pathlib import Path
from backend.storage.manager import StorageManager


def test_path_safety_traversal_prevention(tmp_path: Path):
    manager = StorageManager(base_data_dir=tmp_path)
    image_id = manager.generate_image_id()

    # Attempt path traversal
    with pytest.raises(ValueError, match="Path traversal detected"):
        manager.get_upload_path(image_id, "../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal detected"):
        manager.get_upload_path(image_id, "../../../windows/system32/cmd.exe")


def test_path_safety_sanitization(tmp_path: Path):
    manager = StorageManager(base_data_dir=tmp_path)

    clean = manager.sanitize_filename("my satellite image (1) #2.tif")
    assert " " not in clean
    assert "#" not in clean
    assert clean.endswith(".tif")


def test_path_safety_bytes_save_and_retrieve(tmp_path: Path):
    manager = StorageManager(base_data_dir=tmp_path)
    img_id = manager.generate_image_id()
    data = b"dummy raster header"

    saved_path = manager.save_bytes(data, img_id, "test_raster.tif")
    assert saved_path.exists()
    assert saved_path.read_bytes() == data

    found_path = manager.find_image_path(img_id)
    assert found_path == saved_path
