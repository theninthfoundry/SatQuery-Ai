"""CRS inspection, validation, and coordinate reference management."""

from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    import rasterio.crs
    import pyproj
    HAS_GEO = True
except ImportError:  # pragma: no cover
    HAS_GEO = False


@dataclass
class CRSInfo:
    present: bool
    valid: bool
    epsg: Optional[int]
    name: Optional[str]
    crs_type: str  # "projected", "geographic", "compound", "unknown", "missing"
    status: str    # "ok", "warning", "missing"
    wkt: Optional[str] = None
    proj4: Optional[str] = None
    units: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "present": self.present,
            "valid": self.valid,
            "epsg": self.epsg,
            "name": self.name,
            "type": self.crs_type,
            "status": self.status,
            "units": self.units,
        }


def inspect_crs(crs_input: Any) -> CRSInfo:
    """Inspect and validate CRS from a rasterio dataset CRS, pyproj CRS, EPSG int, or string."""
    if crs_input is None:
        return CRSInfo(
            present=False,
            valid=False,
            epsg=None,
            name=None,
            crs_type="missing",
            status="warning",
            units=None,
        )

    # If it's already an empty rasterio CRS
    if hasattr(crs_input, "is_valid") and not crs_input.is_valid:
        return CRSInfo(
            present=False,
            valid=False,
            epsg=None,
            name=None,
            crs_type="missing",
            status="warning",
            units=None,
        )

    try:
        if HAS_GEO:
            # Handle rasterio.crs.CRS or pyproj.crs.CRS or string/int
            if isinstance(crs_input, rasterio.crs.CRS):
                epsg = crs_input.to_epsg()
                wkt = crs_input.to_wkt()
                proj4 = crs_input.to_proj4()
                is_proj = crs_input.is_projected
                is_geographic = crs_input.is_geographic
                linear_units = getattr(crs_input, "linear_units", None)
            else:
                pyproj_crs = pyproj.CRS.from_user_input(crs_input)
                epsg = pyproj_crs.to_epsg()
                wkt = pyproj_crs.to_wkt()
                proj4 = pyproj_crs.to_proj4()
                is_proj = pyproj_crs.is_projected
                is_geographic = pyproj_crs.is_geographic
                linear_units = pyproj_crs.axis_info[0].unit_name if pyproj_crs.axis_info else None

            if is_proj:
                crs_type = "projected"
                units = linear_units or "metre"
            elif is_geographic:
                crs_type = "geographic"
                units = "degree"
            else:
                crs_type = "unknown"
                units = linear_units

            name = None
            if epsg:
                name = f"EPSG:{epsg}"
                if HAS_GEO:
                    try:
                        p_crs = pyproj.CRS.from_epsg(epsg)
                        name = f"EPSG:{epsg} ({p_crs.name})"
                    except Exception:
                        pass

            return CRSInfo(
                present=True,
                valid=True,
                epsg=epsg,
                name=name or (f"EPSG:{epsg}" if epsg else "Custom CRS"),
                crs_type=crs_type,
                status="ok",
                wkt=wkt,
                proj4=proj4,
                units=units,
            )
        else:
            # Fallback without pyproj
            crs_str = str(crs_input)
            epsg = None
            if "EPSG:" in crs_str.upper():
                try:
                    epsg = int(crs_str.upper().split("EPSG:")[-1].strip().split()[0])
                except ValueError:
                    pass

            return CRSInfo(
                present=True,
                valid=True,
                epsg=epsg,
                name=f"EPSG:{epsg}" if epsg else crs_str,
                crs_type="projected" if epsg and epsg != 4326 else ("geographic" if epsg == 4326 else "unknown"),
                status="ok",
                wkt=None,
                proj4=None,
                units="metre" if epsg and epsg != 4326 else "degree",
            )
    except Exception as e:
        return CRSInfo(
            present=True,
            valid=False,
            epsg=None,
            name=str(crs_input),
            crs_type="unknown",
            status="warning",
            wkt=str(e),
        )


def detect_crs_from_tags(tags: Dict[str, Any]) -> Optional[str]:
    """Attempt to detect a valid CRS string or EPSG from metadata tags."""
    if not tags:
        return None
    for key in ("CRS", "PROJECTION", "crs", "projection", "epsg", "EPSG"):
        if key in tags and tags[key]:
            val = str(tags[key]).strip()
            info = inspect_crs(val)
            if info.valid and info.status == "ok":
                return val
    return None


def is_projected_crs(crs_input: Any) -> bool:
    """Check if a given CRS string, EPSG code, or CRS object represents a projected coordinate system."""
    if not crs_input:
        return False
    if isinstance(crs_input, str):
        s = crs_input.strip().upper()
        if "UTM" in s:
            return True
        if s in ("EPSG:4326", "WGS84", "WGS 84", "CRS84", "OGC:CRS84"):
            return False
    info = inspect_crs(crs_input)
    return info.valid and info.crs_type == "projected"


def reproject_bounds_wgs84(bounds: Any, src_crs: Any) -> Optional[Dict[str, float]]:
    """Reproject bounding box coordinates to WGS84 (EPSG:4326)."""
    if not bounds or not src_crs or not HAS_GEO:
        return None
    try:
        transformer = pyproj.Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
        if isinstance(bounds, (list, tuple)) and len(bounds) == 4:
            minx, miny, maxx, maxy = bounds
        elif isinstance(bounds, dict):
            minx = bounds.get("min_x", bounds.get("xmin", bounds.get("min_lon", 0.0)))
            miny = bounds.get("min_y", bounds.get("ymin", bounds.get("min_lat", 0.0)))
            maxx = bounds.get("max_x", bounds.get("xmax", bounds.get("max_lon", 0.0)))
            maxy = bounds.get("max_y", bounds.get("ymax", bounds.get("max_lat", 0.0)))
        else:
            return None
        min_lon, min_lat = transformer.transform(minx, miny)
        max_lon, max_lat = transformer.transform(maxx, maxy)
        return {
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
        }
    except Exception:
        return None

