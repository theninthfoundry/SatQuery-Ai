"""Unit tests for Visual Grounding coordinate transformation."""

from backend.pipelines.grounding import transform_box_to_geojson_polygon


def test_transform_box_to_geojson_polygon_projected():
    # Box in normalized coordinates (0.25 to 0.75)
    box = {"ymin": 0.25, "xmin": 0.25, "ymax": 0.75, "xmax": 0.75}
    width, height = 100, 100
    # Affine transform: origin (500000, 3000000), 10m pixel size
    # x = 10 * px + 500000
    # y = -10 * py + 3000000
    transform = [10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0]

    geojson_poly, area_m2 = transform_box_to_geojson_polygon(
        box=box,
        width=width,
        height=height,
        transform=transform,
        epsg=32643,  # UTM
    )

    assert geojson_poly["type"] == "Polygon"
    coords = geojson_poly["coordinates"][0]
    assert len(coords) == 5  # 4 corners + closed loop

    # Pixel range: x from 25 to 75 (50 pixels = 500m), y from 25 to 75 (50 pixels = 500m)
    # Area = 500m * 500m = 250,000 m²
    assert area_m2 == 250000.0
