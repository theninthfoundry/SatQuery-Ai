"""AOI Importer supporting GeoJSON, KML, KMZ, and Shapefile ZIP archives.

Provides secure ingestion against Zip Slip, archive bombs, and malformed geometries.
Extracts valid Shapely geometries, repairs self-intersections, detects CRS,
reprojects to WGS84 (EPSG:4326), and computes geodesic area and perimeter.
"""

from dataclasses import dataclass, field
import io
import json
import os
from pathlib import Path
import struct
from typing import Dict, Any, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET
import zipfile

import pyproj
from pyproj import Geod, Transformer
from shapely.geometry import Polygon, MultiPolygon, shape, mapping
from shapely.ops import transform as shapely_transform
import shapely

MAX_UNCOMPRESSED_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_FILES_IN_ARCHIVE = 100


@dataclass
class AOIParseResult:
    success: bool
    name: str
    geometry: Optional[Dict[str, Any]] = None
    crs: str = "EPSG:4326"
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    area_m2: Optional[float] = None
    area_ha: Optional[float] = None
    perimeter_m: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "name": self.name,
            "geometry": self.geometry,
            "crs": self.crs,
            "bbox": self.bbox,
            "area_m2": self.area_m2,
            "area_ha": self.area_ha,
            "perimeter_m": self.perimeter_m,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _validate_and_sanitize_archive(z: zipfile.ZipFile) -> None:
    """Check against zip slip, directory traversal, and compression bombs."""
    total_uncompressed = 0
    infolist = z.infolist()
    if len(infolist) > MAX_FILES_IN_ARCHIVE:
        raise ValueError(f"Archive contains too many files ({len(infolist)} > {MAX_FILES_IN_ARCHIVE})")

    for info in infolist:
        # Check zip slip
        filename = info.filename
        if filename.startswith("/") or ".." in filename or filename.startswith("\\"):
            raise ValueError(f"Dangerous path in archive: {filename}")
        total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
            raise ValueError(
                f"Archive exceeds uncompressed size limit ({MAX_UNCOMPRESSED_SIZE_BYTES // (1024*1024)} MB)"
            )


def _repair_and_finalize_geometry(
    geom: Any,
    src_crs_str: Optional[str] = None,
) -> Tuple[Any, List[float], float, float, float, List[str]]:
    """Ensure geometry is valid, reproject to WGS84 if needed, and compute geodesic metrics."""
    warnings: List[str] = []

    # 1. Geometry validity & repair
    if not geom.is_valid:
        warnings.append("Geometry is self-intersecting or invalid; applying automatic topological repair.")
        if hasattr(shapely, "make_valid"):
            geom = shapely.make_valid(geom)
        else:
            geom = geom.buffer(0)

    if geom.is_empty:
        raise ValueError("Geometry is empty after repair")

    # If it repaired into a GeometryCollection, extract Polygons / MultiPolygons
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if not polys:
            raise ValueError("Repaired geometry contains no valid polygonal components")
        if len(polys) == 1:
            geom = polys[0]
        else:
            flat_polys = []
            for p in polys:
                if p.geom_type == "Polygon":
                    flat_polys.append(p)
                else:
                    flat_polys.extend(p.geoms)
            geom = MultiPolygon(flat_polys)

    # 2. CRS Reprojection to EPSG:4326 if necessary
    src_crs = None
    if src_crs_str:
        try:
            src_crs = pyproj.CRS.from_user_input(src_crs_str)
        except Exception:
            warnings.append(f"Unrecognized source CRS '{src_crs_str}', assuming WGS84 (EPSG:4326)")

    if src_crs and src_crs.to_epsg() != 4326:
        try:
            transformer = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
            geom = shapely_transform(transformer.transform, geom)
        except Exception as e:
            warnings.append(f"Failed to reproject from {src_crs_str} to EPSG:4326: {e}")

    # 3. Geodesic area and perimeter on WGS84 ellipsoid
    geod = Geod(ellps="WGS84")
    poly_area, poly_peri = geod.geometry_area_perimeter(geom)
    area_m2 = abs(float(poly_area))
    area_ha = round(area_m2 / 10000.0, 4)
    perimeter_m = round(abs(float(poly_peri)), 2)
    bbox = [round(x, 6) for x in geom.bounds]

    return geom, bbox, round(area_m2, 2), area_ha, perimeter_m, warnings


def parse_geojson(content: Union[str, bytes], name: str = "AOI") -> AOIParseResult:
    """Parse GeoJSON string or bytes into a validated AOI."""
    warnings: List[str] = []
    errors: List[str] = []

    try:
        data = json.loads(content if isinstance(content, str) else content.decode("utf-8"))
    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"Invalid JSON: {str(e)}"])

    # Extract geometry
    crs_str = "EPSG:4326"

    # Check named CRS in GeoJSON
    if "crs" in data and isinstance(data["crs"], dict):
        props = data["crs"].get("properties", {})
        crs_name = props.get("name", "")
        if crs_name:
            crs_str = crs_name

    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
        if not features:
            return AOIParseResult(success=False, name=name, errors=["FeatureCollection is empty"])
        poly_list = []
        for feat in features:
            f_geom = feat.get("geometry")
            if f_geom and f_geom.get("type") in ("Polygon", "MultiPolygon"):
                s_geom = shape(f_geom)
                if s_geom.is_valid and not s_geom.is_empty:
                    poly_list.append(s_geom)
        if not poly_list:
            return AOIParseResult(success=False, name=name, errors=["No polygon features found in FeatureCollection"])
        if len(poly_list) == 1:
            geom = poly_list[0]
        else:
            geom = MultiPolygon([p if p.geom_type == "Polygon" else p.geoms[0] for p in poly_list])
    elif data.get("type") == "Feature":
        f_geom = data.get("geometry")
        if not f_geom or f_geom.get("type") not in ("Polygon", "MultiPolygon"):
            return AOIParseResult(success=False, name=name, errors=["Feature geometry must be Polygon or MultiPolygon"])
        geom = shape(f_geom)
    elif data.get("type") in ("Polygon", "MultiPolygon"):
        geom = shape(data)
    else:
        return AOIParseResult(
            success=False,
            name=name,
            errors=[f"Unsupported GeoJSON object type '{data.get('type')}'. Must be FeatureCollection, Feature, or Polygon."],
        )

    try:
        final_geom, bbox, area_m2, area_ha, perimeter_m, repair_warns = _repair_and_finalize_geometry(geom, crs_str)
        warnings.extend(repair_warns)
        return AOIParseResult(
            success=True,
            name=name,
            geometry=mapping(final_geom),
            crs="EPSG:4326",
            bbox=bbox,
            area_m2=area_m2,
            area_ha=area_ha,
            perimeter_m=perimeter_m,
            warnings=warnings,
            errors=errors,
        )
    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"Geometry processing failed: {str(e)}"])


def _parse_kml_coordinates(coord_str: str) -> List[Tuple[float, float]]:
    """Parse KML lon,lat[,alt] coordinate string into [(lon, lat), ...]."""
    coords = []
    tokens = coord_str.strip().split()
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        parts = tok.split(",")
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                coords.append((lon, lat))
            except ValueError:
                continue
    return coords


def parse_kml(content: Union[str, bytes], name: str = "AOI") -> AOIParseResult:
    """Parse KML content into an AOI geometry."""
    warnings: List[str] = []
    errors: List[str] = []

    try:
        xml_bytes = content.encode("utf-8") if isinstance(content, str) else content
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"Invalid KML XML: {str(e)}"])

    # Find Polygon elements irrespective of XML namespace
    polygons: List[Polygon] = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "Polygon":
            exterior_coords: List[Tuple[float, float]] = []
            interiors: List[List[Tuple[float, float]]] = []

            for child in elem.iter():
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == "outerBoundaryIs":
                    for sub in child.iter():
                        stag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                        if stag == "coordinates" and sub.text:
                            exterior_coords = _parse_kml_coordinates(sub.text)
                elif ctag == "innerBoundaryIs":
                    for sub in child.iter():
                        stag = sub.tag.split("}")[-1] if "}" in sub.tag else sub.tag
                        if stag == "coordinates" and sub.text:
                            inner_coords = _parse_kml_coordinates(sub.text)
                            if len(inner_coords) >= 3:
                                interiors.append(inner_coords)

            if len(exterior_coords) >= 3:
                try:
                    poly = Polygon(exterior_coords, holes=interiors)
                    if not poly.is_empty:
                        polygons.append(poly)
                except Exception as e:
                    warnings.append(f"Skipped malformed KML polygon: {e}")

    if not polygons:
        return AOIParseResult(success=False, name=name, errors=["No valid Polygon found in KML"])

    geom = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)

    try:
        final_geom, bbox, area_m2, area_ha, perimeter_m, repair_warns = _repair_and_finalize_geometry(geom, "EPSG:4326")
        warnings.extend(repair_warns)
        return AOIParseResult(
            success=True,
            name=name,
            geometry=mapping(final_geom),
            crs="EPSG:4326",
            bbox=bbox,
            area_m2=area_m2,
            area_ha=area_ha,
            perimeter_m=perimeter_m,
            warnings=warnings,
            errors=errors,
        )
    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"KML geometry processing failed: {str(e)}"])


def parse_kmz(kmz_input: Union[bytes, Path, str], name: str = "AOI") -> AOIParseResult:
    """Safely extract and parse doc.kml from a KMZ archive."""
    try:
        if isinstance(kmz_input, (str, Path)):
            f_in = open(kmz_input, "rb")
        else:
            f_in = io.BytesIO(kmz_input)

        with zipfile.ZipFile(f_in, "r") as z:
            _validate_and_sanitize_archive(z)
            kml_filename = None
            for name_in_zip in z.namelist():
                if name_in_zip.lower().endswith(".kml"):
                    kml_filename = name_in_zip
                    break

            if not kml_filename:
                return AOIParseResult(success=False, name=name, errors=["KMZ does not contain a .kml file"])

            kml_content = z.read(kml_filename)
            return parse_kml(kml_content, name=name)
    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"KMZ extraction error: {str(e)}"])


def parse_shapefile_zip(zip_input: Union[bytes, Path, str], name: str = "AOI") -> AOIParseResult:
    """Parse ESRI Shapefile polygon records from a safe ZIP archive."""
    try:
        if isinstance(zip_input, (str, Path)):
            f_in = open(zip_input, "rb")
        else:
            f_in = io.BytesIO(zip_input)

        with zipfile.ZipFile(f_in, "r") as z:
            _validate_and_sanitize_archive(z)

            shp_file = None
            prj_file = None
            for fname in z.namelist():
                lower = fname.lower()
                if lower.endswith(".shp"):
                    shp_file = fname
                elif lower.endswith(".prj"):
                    prj_file = fname

            if not shp_file:
                return AOIParseResult(success=False, name=name, errors=["ZIP does not contain a .shp file"])

            shp_bytes = z.read(shp_file)
            prj_str = None
            if prj_file:
                try:
                    prj_str = z.read(prj_file).decode("utf-8", errors="ignore")
                except Exception:
                    pass

        # Parse .shp format
        if len(shp_bytes) < 100:
            return AOIParseResult(success=False, name=name, errors=["Corrupt or truncated .shp file header"])

        # File header: Big-endian file code (9994)
        file_code = struct.unpack(">I", shp_bytes[0:4])[0]
        if file_code != 9994:
            return AOIParseResult(success=False, name=name, errors=[f"Invalid Shapefile header magic: {file_code}"])

        header_shape_type = struct.unpack("<i", shp_bytes[32:36])[0]
        if header_shape_type not in (5, 15, 25):
            return AOIParseResult(
                success=False,
                name=name,
                errors=[
                    f"Shapefile shape type {header_shape_type} is not a Polygon. "
                    "SatQuery AOI ingestion requires polygonal geometry."
                ],
            )

        offset = 100
        polygons: List[Polygon] = []

        while offset + 8 <= len(shp_bytes):
            rec_num, content_len = struct.unpack(">2I", shp_bytes[offset : offset + 8])
            offset += 8
            content_bytes = content_len * 2
            if offset + content_bytes > len(shp_bytes):
                break

            record_data = shp_bytes[offset : offset + content_bytes]
            offset += content_bytes

            if len(record_data) < 44:
                continue

            rec_shape_type = struct.unpack("<i", record_data[0:4])[0]
            if rec_shape_type not in (5, 15, 25):
                continue

            num_parts, num_points = struct.unpack("<2i", record_data[36:44])
            parts_offset = 44
            points_offset = parts_offset + (num_parts * 4)

            if points_offset + (num_points * 16) > len(record_data):
                continue

            parts = list(struct.unpack(f"<{num_parts}i", record_data[parts_offset:points_offset]))
            parts.append(num_points)

            rings = []
            for i in range(num_parts):
                start_idx = parts[i]
                end_idx = parts[i + 1]
                ring_coords = []
                for p_idx in range(start_idx, end_idx):
                    p_offset = points_offset + (p_idx * 16)
                    x, y = struct.unpack("<2d", record_data[p_offset : p_offset + 16])
                    ring_coords.append((x, y))
                if len(ring_coords) >= 3:
                    rings.append(ring_coords)

            if rings:
                try:
                    poly = Polygon(rings[0], holes=rings[1:])
                    if not poly.is_empty:
                        polygons.append(poly)
                except Exception:
                    pass

        if not polygons:
            return AOIParseResult(success=False, name=name, errors=["No valid Polygon features extracted from Shapefile"])

        geom = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)

        final_geom, bbox, area_m2, area_ha, perimeter_m, repair_warns = _repair_and_finalize_geometry(geom, prj_str)
        return AOIParseResult(
            success=True,
            name=name,
            geometry=mapping(final_geom),
            crs="EPSG:4326",
            bbox=bbox,
            area_m2=area_m2,
            area_ha=area_ha,
            perimeter_m=perimeter_m,
            warnings=repair_warns,
            errors=[],
        )

    except Exception as e:
        return AOIParseResult(success=False, name=name, errors=[f"Shapefile ZIP parsing failed: {str(e)}"])


def import_aoi_file(
    content: bytes,
    filename: str,
    custom_name: Optional[str] = None,
) -> AOIParseResult:
    """Universal dispatcher to parse any supported AOI file format."""
    lower = filename.lower()
    base_name = custom_name or Path(filename).stem

    if lower.endswith(".geojson") or lower.endswith(".json"):
        return parse_geojson(content, name=base_name)
    elif lower.endswith(".kml"):
        return parse_kml(content, name=base_name)
    elif lower.endswith(".kmz"):
        return parse_kmz(content, name=base_name)
    elif lower.endswith(".zip"):
        return parse_shapefile_zip(content, name=base_name)
    else:
        return AOIParseResult(
            success=False,
            name=base_name,
            errors=[
                f"Unsupported file format '{Path(filename).suffix}'. "
                "Supported formats: .geojson, .json, .kml, .kmz, .zip (ESRI Shapefile)"
            ],
        )
