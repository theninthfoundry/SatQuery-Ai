"""Geospatial raster and image validation engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from .metadata import RasterMetadata

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".geotif", ".geotiff", ".png", ".jpg", ".jpeg"}


@dataclass
class ValidationResult:
    valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def validate_file_path(
    filepath: Path | str,
    max_size_mb: int = 512,
) -> ValidationResult:
    """Validate file path, extension, existence, and size before raster parsing."""
    p = Path(filepath)
    warnings: List[str] = []
    errors: List[str] = []

    if not p.exists():
        return ValidationResult(valid=False, errors=[f"File does not exist: {p.name}"])

    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            valid=False,
            errors=[f"Unsupported file format '{p.suffix}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"],
        )

    file_size_bytes = p.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > max_size_mb:
        errors.append(f"File size ({file_size_mb:.2f} MB) exceeds maximum limit ({max_size_mb} MB)")

    if file_size_bytes == 0:
        errors.append("File is empty (0 bytes)")

    return ValidationResult(valid=len(errors) == 0, warnings=warnings, errors=errors)


def validate_raster_metadata(
    meta: RasterMetadata,
    strict_crs: bool = False,
) -> ValidationResult:
    """Validate extracted raster metadata (dimensions, band counts, CRS, values)."""
    warnings: List[str] = []
    errors: List[str] = []

    # 1. Dimensions check
    if meta.width <= 0 or meta.height <= 0:
        errors.append(f"Invalid raster dimensions: {meta.width}x{meta.height}")
    elif meta.width > 32768 or meta.height > 32768:
        warnings.append(f"Very large raster dimensions ({meta.width}x{meta.height}); windowed processing will be used.")

    # 2. Band count check
    if meta.band_count <= 0:
        errors.append(f"Invalid band count: {meta.band_count}")
    elif meta.band_count > 1024:
        errors.append(f"Exceedingly high band count ({meta.band_count})")

    # 3. CRS validation
    if not meta.crs.present:
        msg = "Image lacks geospatial Coordinate Reference System (CRS). Ground coordinate transformations will not be possible."
        if strict_crs:
            errors.append(msg)
        else:
            warnings.append(msg)
    elif not meta.crs.valid:
        warnings.append(f"CRS is unparseable or non-standard: {meta.crs.name}")

    # 4. Band value validity
    for b in meta.bands:
        if b.min is not None and b.max is not None and b.min > b.max:
            errors.append(f"Corrupt statistical values in Band {b.band_index} (min > max)")

    is_valid = len(errors) == 0
    return ValidationResult(valid=is_valid, warnings=warnings, errors=errors)
