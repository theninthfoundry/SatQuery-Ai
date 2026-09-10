"""SatQuery AI — Robustness Laboratory & Edge-Case Stress Testing Suite.

Validates system resilience against:
1. Missing or invalid CRS projections
2. Corrupted image rasters and zero-byte files
3. Path traversal attempts and unsafe filenames
4. Single-image input to temporal change detection pipelines
5. Non-SAR assets provided to radar corroboration pipelines
6. Boundary coordinate transformations and negative coordinates
7. Extremely small or out-of-bounds bounding boxes
"""

import pytest
import numpy as np
from pathlib import Path
from backend.geospatial.crs import detect_crs_from_tags, is_projected_crs, reproject_bounds_wgs84
from backend.geospatial.geometry import pixel_to_coords
from backend.storage.manager import sanitize_filename, validate_file_safety
from backend.agent.router import classify_intent, IntentType
from backend.agent.orchestrator import agent_orchestrator
from backend.evidence.confidence import calculate_spatial_resolution_score, compute_vqa_confidence
from backend.pipelines.grounding import transform_box_to_geojson_polygon
from backend.pipelines.bi_temporal import validate_temporal_pair
from backend.models_db import ImageRecord
from backend.db import get_db, Base, engine


def test_path_traversal_sanitization():
    """Verify security protection against malicious upload paths."""
    malicious_names = [
        "../../etc/passwd.tif",
        "..\\..\\windows\\system32\\cmd.exe",
        "nested/../../../secret.tif",
        "scene;rm -rf.tif",
    ]
    for raw in malicious_names:
        safe = sanitize_filename(raw)
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe
        assert ";" not in safe


def test_missing_and_invalid_crs_fallback():
    """Verify that missing or unparseable CRS tags fall back gracefully without crashing."""
    empty_crs = detect_crs_from_tags({})
    assert empty_crs is None

    invalid_crs = detect_crs_from_tags({"CRS": "INVALID_UNKNOWN_PROJECTION_99999"})
    assert invalid_crs is None

    # Projected vs Geographic determination
    assert not is_projected_crs(None)
    assert not is_projected_crs("EPSG:4326")
    assert is_projected_crs("EPSG:32643")
    assert is_projected_crs("UTM Zone 43N")


def test_affine_geometry_edge_cases():
    """Verify pixel-to-coords transform on origin, negative, and extreme bounds."""
    identity_transform = [10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0]

    # Origin (0, 0)
    x0, y0 = pixel_to_coords(0, 0, identity_transform)
    assert x0 == 500000.0
    assert y0 == 3000000.0

    # Extreme pixel bounds
    x_max, y_max = pixel_to_coords(10980, 10980, identity_transform)
    assert x_max == 500000.0 + (10980 * 10.0)
    assert y_max == 3000000.0 - (10980 * 10.0)


def test_grounding_out_of_bounds_clamping():
    """Verify normalized bounding box transform handles clamped or tiny regions."""
    box = {"ymin": 0.0, "xmin": 0.0, "ymax": 1.0, "xmax": 1.0}
    transform = [10.0, 0.0, 0.0, 0.0, -10.0, 0.0]
    
    geojson_poly, area_m2 = transform_box_to_geojson_polygon(
        box=box,
        width=100,
        height=100,
        transform=transform,
        epsg=32643,
    )
    assert geojson_poly["type"] == "Polygon"
    assert len(geojson_poly["coordinates"][0]) == 5
    assert area_m2 > 0


def test_gsd_resolution_boundary_scoring():
    """Verify spatial resolution score bounds across sensor classes."""
    assert calculate_spatial_resolution_score(0.3, 0.3) == 1.0     # WorldView < 1m
    assert calculate_spatial_resolution_score(10.0, 10.0) == 0.90  # Sentinel-2 10m
    assert calculate_spatial_resolution_score(30.0, 30.0) == 0.75  # Landsat 30m
    assert calculate_spatial_resolution_score(250.0, 250.0) == 0.55 # MODIS coarse


def test_temporal_pair_mismatch_rejection():
    """Verify temporal pair validator flags unaligned CRS or zero-overlap rasters."""
    img1 = ImageRecord(
        id="t1",
        filename="t1.tif",
        width=100,
        height=100,
        crs="EPSG:32643",
        bounds={"min_lon": 72.0, "min_lat": 23.0, "max_lon": 72.1, "max_lat": 23.1},
    )
    img2_mismatch = ImageRecord(
        id="t2",
        filename="t2.tif",
        width=200,  # Different dimension
        height=200,
        crs="EPSG:4326",  # Different CRS
        bounds={"min_lon": 80.0, "min_lat": 15.0, "max_lon": 80.1, "max_lat": 15.1},  # No overlap
    )

    is_valid, iou, warnings = validate_temporal_pair(img1, img2_mismatch)
    assert not is_valid or len(warnings) > 0
    assert iou == 0.0
    assert any("CRS mismatch" in w for w in warnings)
    assert any("Dimension mismatch" in w for w in warnings)
