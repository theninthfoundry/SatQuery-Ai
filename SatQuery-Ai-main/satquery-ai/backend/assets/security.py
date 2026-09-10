"""Input Sanitization & Security for uploaded Earth Observation assets.

Protects against:
1. Oversized files (denial-of-service via VRAM/disk exhaustion)
2. Invalid file types (non-raster files disguised as GeoTIFFs)
3. Decompression bombs (tiny file → huge decompressed raster)
4. Path traversal (../ in filenames)
5. Corrupted or truncated rasters
6. NaN/Inf contamination in raster data
7. Excessively large dimensions or band counts
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class SanitizationResult:
    """Result of input sanitization checks."""
    safe: bool
    filename: str
    file_size_bytes: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe": self.safe,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "sanitized_filename": self.sanitized_filename,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class InputSanitizer:
    """Comprehensive input validation for uploaded raster files."""

    # Configurable limits
    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    MAX_DIMENSION: int = 50_000  # 50k pixels per side
    MAX_BAND_COUNT: int = 256
    MAX_PIXEL_COUNT: int = 500_000_000  # 500 million pixels
    ALLOWED_EXTENSIONS: set = {
        ".tif", ".tiff", ".geotif", ".geotiff",
        ".png", ".jpg", ".jpeg", ".jp2",
    }

    # Magic bytes for common raster formats
    MAGIC_BYTES = {
        b"\x49\x49\x2a\x00": "TIFF (little-endian)",
        b"\x4d\x4d\x00\x2a": "TIFF (big-endian)",
        b"\x49\x49\x2b\x00": "BigTIFF (little-endian)",
        b"\x4d\x4d\x00\x2b": "BigTIFF (big-endian)",
        b"\x89\x50\x4e\x47": "PNG",
        b"\xff\xd8\xff": "JPEG",
    }

    def sanitize(self, filepath: Path | str, original_filename: str = "") -> SanitizationResult:
        """Run all sanitization checks on an uploaded file.

        Args:
            filepath: Path to the uploaded file on disk.
            original_filename: The original filename from the upload (may contain unsafe chars).

        Returns:
            SanitizationResult indicating whether the file is safe to process.
        """
        p = Path(filepath)
        fname = original_filename or p.name
        errors: List[str] = []
        warnings: List[str] = []

        if not p.exists():
            return SanitizationResult(
                safe=False, filename=fname, file_size_bytes=0,
                errors=["File does not exist."],
            )

        file_size = p.stat().st_size

        # 1. Filename sanitization
        sanitized_name = self._sanitize_filename(fname)
        if sanitized_name != fname:
            warnings.append(
                f"Filename sanitized: '{fname}' → '{sanitized_name}'"
            )

        # 2. Path traversal check
        if ".." in str(p) or ".." in fname:
            errors.append("Path traversal detected in filename.")

        # 3. File size check
        if file_size > self.MAX_FILE_SIZE_BYTES:
            errors.append(
                f"File size ({file_size / (1024**3):.2f} GB) exceeds "
                f"maximum allowed ({self.MAX_FILE_SIZE_BYTES / (1024**3):.0f} GB)."
            )

        if file_size == 0:
            errors.append("File is empty (0 bytes).")

        # 4. Extension check
        ext = p.suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            errors.append(
                f"File extension '{ext}' is not in the allowed list: "
                f"{', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # 5. Magic byte validation
        if file_size > 0:
            magic_result = self._check_magic_bytes(p)
            if magic_result is None:
                warnings.append(
                    "Could not identify file format from magic bytes. "
                    "File may be corrupted or in an unsupported format."
                )

        # 6. Raster-specific checks (dimensions, bands, decompression bomb)
        if file_size > 0 and ext in (".tif", ".tiff", ".geotif", ".geotiff"):
            raster_errors, raster_warnings = self._check_raster_properties(p)
            errors.extend(raster_errors)
            warnings.extend(raster_warnings)
        elif file_size > 0 and ext in (".png", ".jpg", ".jpeg"):
            img_errors, img_warnings = self._check_image_properties(p)
            errors.extend(img_errors)
            warnings.extend(img_warnings)

        return SanitizationResult(
            safe=len(errors) == 0,
            filename=fname,
            file_size_bytes=file_size,
            errors=errors,
            warnings=warnings,
            sanitized_filename=sanitized_name,
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Remove unsafe characters from filename, preserving extension."""
        # Remove path components
        name = Path(filename).name
        # Remove null bytes and control characters
        name = re.sub(r"[\x00-\x1f\x7f]", "", name)
        # Remove potentially dangerous characters
        name = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Collapse multiple underscores
        name = re.sub(r"_+", "_", name)
        # Remove leading/trailing whitespace and dots
        name = name.strip(". ")
        return name if name else "untitled.tif"

    def _check_magic_bytes(self, filepath: Path) -> Optional[str]:
        """Validate file magic bytes against known raster formats."""
        try:
            with open(filepath, "rb") as f:
                header = f.read(8)
        except IOError:
            return None

        for magic, fmt_name in self.MAGIC_BYTES.items():
            if header[:len(magic)] == magic:
                return fmt_name
        return None

    def _check_raster_properties(self, filepath: Path) -> tuple:
        """Validate GeoTIFF raster properties for decompression bombs and corruption."""
        errors: List[str] = []
        warnings: List[str] = []

        try:
            import rasterio
        except ImportError:
            warnings.append("rasterio not available — skipping raster validation.")
            return errors, warnings

        try:
            with rasterio.open(filepath) as ds:
                # Dimension checks
                if ds.width > self.MAX_DIMENSION or ds.height > self.MAX_DIMENSION:
                    errors.append(
                        f"Raster dimensions ({ds.width}×{ds.height}) exceed "
                        f"maximum ({self.MAX_DIMENSION}×{self.MAX_DIMENSION})."
                    )

                # Pixel count check (decompression bomb)
                pixel_count = ds.width * ds.height * ds.count
                if pixel_count > self.MAX_PIXEL_COUNT:
                    errors.append(
                        f"Total pixel count ({pixel_count:,}) exceeds maximum "
                        f"({self.MAX_PIXEL_COUNT:,}). Possible decompression bomb."
                    )

                # Band count check
                if ds.count > self.MAX_BAND_COUNT:
                    errors.append(
                        f"Band count ({ds.count}) exceeds maximum ({self.MAX_BAND_COUNT})."
                    )

                # Decompression ratio check
                compressed_size = filepath.stat().st_size
                # Estimate uncompressed size
                dtype_bytes = {"uint8": 1, "int16": 2, "uint16": 2,
                               "int32": 4, "uint32": 4, "float32": 4, "float64": 8}
                bpp = dtype_bytes.get(str(ds.dtypes[0]), 4) if ds.dtypes else 4
                uncompressed_estimate = ds.width * ds.height * ds.count * bpp

                if compressed_size > 0:
                    ratio = uncompressed_estimate / compressed_size
                    if ratio > 1000:
                        errors.append(
                            f"Suspicious compression ratio ({ratio:.0f}:1). "
                            "Possible decompression bomb."
                        )
                    elif ratio > 100:
                        warnings.append(
                            f"High compression ratio ({ratio:.0f}:1)."
                        )

                # Check for NaN/Inf contamination (sample first band)
                if HAS_NUMPY:
                    try:
                        sample = ds.read(
                            1,
                            window=rasterio.windows.Window(
                                0, 0, min(ds.width, 512), min(ds.height, 512)
                            ),
                        )
                        if np.issubdtype(sample.dtype, np.floating):
                            nan_count = int(np.sum(np.isnan(sample)))
                            inf_count = int(np.sum(np.isinf(sample)))
                            total = sample.size
                            if nan_count > 0:
                                warnings.append(
                                    f"NaN values detected in band 1: "
                                    f"{nan_count}/{total} pixels ({nan_count/total:.1%})."
                                )
                            if inf_count > 0:
                                warnings.append(
                                    f"Inf values detected in band 1: "
                                    f"{inf_count}/{total} pixels ({inf_count/total:.1%})."
                                )
                    except Exception:
                        warnings.append("Could not read sample data for NaN/Inf check.")

        except rasterio.errors.RasterioIOError as e:
            errors.append(f"Raster file is corrupted or unreadable: {e}")
        except Exception as e:
            errors.append(f"Unexpected error reading raster: {e}")

        return errors, warnings

    def _check_image_properties(self, filepath: Path) -> tuple:
        """Validate standard image (PNG/JPEG) properties."""
        errors: List[str] = []
        warnings: List[str] = []

        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = self.MAX_PIXEL_COUNT
        except ImportError:
            warnings.append("PIL not available — skipping image validation.")
            return errors, warnings

        try:
            with Image.open(filepath) as img:
                w, h = img.size
                if w > self.MAX_DIMENSION or h > self.MAX_DIMENSION:
                    errors.append(
                        f"Image dimensions ({w}×{h}) exceed "
                        f"maximum ({self.MAX_DIMENSION}×{self.MAX_DIMENSION})."
                    )
                if w * h > self.MAX_PIXEL_COUNT:
                    errors.append(
                        f"Pixel count ({w * h:,}) exceeds maximum. "
                        "Possible decompression bomb."
                    )

                if not filepath.suffix.lower().startswith(".tif"):
                    warnings.append(
                        "Standard image (non-GeoTIFF) uploaded. "
                        "No CRS or georeferencing information available. "
                        "Area measurements will be in pixel units only."
                    )

        except Image.DecompressionBombError:
            errors.append("Decompression bomb detected by PIL.")
        except Exception as e:
            errors.append(f"Image file is corrupted or unreadable: {e}")

        return errors, warnings
