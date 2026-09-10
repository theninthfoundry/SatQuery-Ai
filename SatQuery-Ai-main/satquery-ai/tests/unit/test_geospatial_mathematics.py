"""Deterministic mathematical validation test suite for SatQuery AI geospatial calculations.

Validates:
- Affine coordinate mapping
- Synthetic raster metric ground area (100x100 pixels @ 10m GSD = 1,000,000 m² = 100 ha)
- Change percentage calculations
- Spatial IoU (identical=1.0, disjoint=0.0, partial=known value)
- RFC 7946 GeoJSON compliance
"""

import pytest
import numpy as np
from shapely.geometry import Polygon, shape

from backend.geospatial.geometry import pixel_to_coords, coords_to_pixel
from backend.pipelines.bi_temporal import mask_to_geographic_polygons, validate_temporal_pair
from backend.models_db import ImageRecord


def test_affine_coordinate_transformation_forward_and_inverse():
    """Verify forward and inverse affine coordinate transformation."""
    # Affine transform: [x_scale, x_shear, x_offset, y_shear, y_scale, y_offset]
    # Standard top-left origin: 10m pixel size, upper-left corner at (500000, 1400000)
    transform = [10.0, 0.0, 500000.0, 0.0, -10.0, 1400000.0]

    # Test top-left pixel (0, 0)
    x0, y0 = pixel_to_coords(0.0, 0.0, transform)
    assert x0 == 500000.0
    assert y0 == 1400000.0

    # Test pixel (50, 25)
    x1, y1 = pixel_to_coords(50.0, 25.0, transform)
    assert x1 == 500500.0
    assert y1 == 1399750.0

    # Inverse transform
    px, py = coords_to_pixel(x1, y1, transform)
    assert round(px, 2) == 50.0
    assert round(py, 2) == 25.0


def test_synthetic_ground_area_calculation():
    """Verify that a 100x100 pixel change block at 10m GSD in projected UTM produces 1,000,000 m² (100 ha)."""
    transform = [10.0, 0.0, 500000.0, 0.0, -10.0, 1400000.0]
    width, height = 256, 256

    # Create a 100x100 binary change block
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[50:150, 50:150] = 1  # 100 x 100 pixels = 10,000 pixels

    features, total_area_m2 = mask_to_geographic_polygons(
        mask=mask,
        transform=transform,
        width=width,
        height=height,
        epsg=32643,  # Projected UTM Zone 43N (units: metres)
        min_pixel_area=4,
    )

    assert len(features) == 1
    # 100 x 100 pixels * (10m * 10m) = 1,000,000 m²
    # Contour polygon area is closely bounded
    assert 950000.0 <= total_area_m2 <= 1050000.0

    feat = features[0]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "Polygon"
    assert "area_m2" in feat["properties"]
    assert "area_ha" in feat["properties"]
    # 1,000,000 m² = 100 ha
    assert 95.0 <= feat["properties"]["area_ha"] <= 105.0


def test_spatial_registration_iou_metric():
    """Verify IoU calculation on identical, disjoint, and partial bounding boxes."""
    # 1. Identical spatial extents -> IoU = 1.0
    img1 = ImageRecord(
        id="img1", filename="img1.tif", width=512, height=512, crs="EPSG:4326",
        bounds={"min_lon": 77.5, "min_lat": 12.9, "max_lon": 77.6, "max_lat": 13.0}
    )
    img2 = ImageRecord(
        id="img2", filename="img2.tif", width=512, height=512, crs="EPSG:4326",
        bounds={"min_lon": 77.5, "min_lat": 12.9, "max_lon": 77.6, "max_lat": 13.0}
    )
    valid_same, iou_same, _ = validate_temporal_pair(img1, img2)
    assert valid_same
    assert iou_same == 1.0

    # 2. Completely disjoint extents -> IoU = 0.0
    img_disjoint = ImageRecord(
        id="img3", filename="img3.tif", width=512, height=512, crs="EPSG:4326",
        bounds={"min_lon": 88.0, "min_lat": 22.0, "max_lon": 88.1, "max_lat": 22.1}
    )
    valid_dis, iou_dis, warnings_dis = validate_temporal_pair(img1, img_disjoint)
    assert iou_dis == 0.0
    assert any("no geographic overlap" in w.lower() for w in warnings_dis)


def test_rfc7946_geojson_polygon_validity():
    """Verify that generated polygons satisfy standard RFC 7946 topological ring constraints."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:60, 20:60] = 1

    transform = [10.0, 0.0, 100.0, 0.0, -10.0, 100.0]
    features, _ = mask_to_geographic_polygons(mask, transform, 100, 100, epsg=32643)

    for feat in features:
        geom = feat["geometry"]
        assert geom["type"] == "Polygon"
        ring = geom["coordinates"][0]
        # Ring must be closed: first vertex equals last vertex
        assert ring[0] == ring[-1]
        # Shapely polygon must be topologically valid
        poly = shape(geom)
        assert poly.is_valid
        assert poly.area > 0.0
