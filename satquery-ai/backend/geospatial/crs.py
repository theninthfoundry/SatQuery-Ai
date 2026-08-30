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
