"""Tests for AOI Importer (GeoJSON, KML, KMZ, Shapefile ZIP)."""

import io
import json
import struct
import zipfile
import pytest

from backend.geospatial.aoi_importer import (
    import_aoi_file,
    parse_geojson,
    parse_kml,
    parse_kmz,
    parse_shapefile_zip,
)


def test_import_geojson_valid():
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [78.40, 17.40],
                            [78.45, 17.40],
                            [78.45, 17.45],
                            [78.40, 17.45],
                            [78.40, 17.40],
                        ]
                    ],
                },
                "properties": {"name": "Test AOI"},
            }
        ],
    }
    content = json.dumps(geojson_data).encode("utf-8")
    result = import_aoi_file(content, "test.geojson")
    assert result.success is True
    assert result.geometry["type"] == "Polygon"
    assert result.area_ha > 0
    assert result.perimeter_m > 0
    assert result.bbox == [78.40, 17.40, 78.45, 17.45]


def test_import_geojson_self_intersecting_repair():
    # Bowtie polygon (self-intersecting)
    geojson_data = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0],
                [1.0, 0.0],
                [0.0, 0.0],
            ]
        ],
    }
    content = json.dumps(geojson_data).encode("utf-8")
    result = import_aoi_file(content, "bowtie.json")
    assert result.success is True
    assert len(result.warnings) > 0  # Repaired warning present
    assert result.area_ha > 0


def test_import_kml_valid():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>Hyderabad Test Site</name>
    <Polygon>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>
            78.40,17.40,0 78.45,17.40,0 78.45,17.45,0 78.40,17.45,0 78.40,17.40,0
          </coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>
  </Placemark>
</kml>
"""
    result = import_aoi_file(kml_content.encode("utf-8"), "test.kml")
    assert result.success is True
    assert result.geometry["type"] == "Polygon"
    assert result.area_ha > 0
    assert result.bbox == [78.40, 17.40, 78.45, 17.45]


def test_import_kmz_valid():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Polygon>
    <outerBoundaryIs>
      <LinearRing>
        <coordinates>
          78.40,17.40,0 78.45,17.40,0 78.45,17.45,0 78.40,17.45,0 78.40,17.40,0
        </coordinates>
      </LinearRing>
    </outerBoundaryIs>
  </Polygon>
</kml>
"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("doc.kml", kml_content)
    kmz_bytes = buf.getvalue()

    result = import_aoi_file(kmz_bytes, "test.kmz")
    assert result.success is True
    assert result.geometry["type"] == "Polygon"
    assert result.area_ha > 0


def test_import_shapefile_zip():
    # Synthesize minimal valid .shp with 1 polygon
    # 100 byte header
    header = bytearray(100)
    # File code 9994 (big endian)
    struct.pack_into(">I", header, 0, 9994)
    # File length in 16-bit words (placeholder, update later)
    # Version 1000 (little endian)
    struct.pack_into("<i", header, 28, 1000)
    # Shape type 5 = Polygon
    struct.pack_into("<i", header, 32, 5)
    # Box: minx, miny, maxx, maxy
    struct.pack_into("<4d", header, 36, 78.40, 17.40, 78.45, 17.45)

    # Record 1:
    coords = [
        (78.40, 17.40),
        (78.45, 17.40),
        (78.45, 17.45),
        (78.40, 17.45),
        (78.40, 17.40),
    ]
    rec_body = bytearray()
    # shape type 5
    rec_body.extend(struct.pack("<i", 5))
    # box
    rec_body.extend(struct.pack("<4d", 78.40, 17.40, 78.45, 17.45))
    # num_parts = 1, num_points = 5
    rec_body.extend(struct.pack("<2i", 1, 5))
    # parts: index 0
    rec_body.extend(struct.pack("<i", 0))
    # points:
    for x, y in coords:
        rec_body.extend(struct.pack("<2d", x, y))

    content_len_words = len(rec_body) // 2
    rec_header = struct.pack(">2I", 1, content_len_words)
    record = rec_header + rec_body

    full_shp = bytes(header) + record
    total_len_words = len(full_shp) // 2
    struct.pack_into(">I", header, 24, total_len_words)
    full_shp = bytes(header) + record

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("aoi_boundary.shp", full_shp)
        z.writestr("aoi_boundary.prj", 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')
    zip_bytes = buf.getvalue()

    result = import_aoi_file(zip_bytes, "test_shapefile.zip")
    assert result.success is True
    assert result.geometry["type"] == "Polygon"
    assert result.area_ha > 0
    assert result.bbox == [78.40, 17.40, 78.45, 17.45]


def test_zip_slip_prevention():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../evil.shp", b"malicious data")
    zip_bytes = buf.getvalue()

    result = import_aoi_file(zip_bytes, "exploit.zip")
    assert result.success is False
    assert any("Dangerous path" in err for err in result.errors)
