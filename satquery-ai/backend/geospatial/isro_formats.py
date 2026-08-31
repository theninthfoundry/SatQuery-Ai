"""Native ISRO / Indian Space Research Organisation satellite product definitions and metadata resolvers.

Covers Indian Earth Observation satellites:
- Cartosat-3 & Cartosat-2 (Sub-meter High-Resolution Optical)
- Resourcesat-2 / 2A (LISS-4 & AWiFS Multi-Spectral)
- RISAT-1 / EOS-04 (C-band Synthetic Aperture Radar)
- Oceansat-3 / EOS-06 (Ocean Color Monitor OCM-3)
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ISROSensorProfile:
    satellite_name: str
    sensor_name: str
    modality: str  # "optical" | "sar" | "multispectral" | "hyperspectral"
    nominal_gsd_m: float
    bands: List[str]
    swath_km: float
    polarization: Optional[List[str]] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "satellite_name": self.satellite_name,
            "sensor_name": self.sensor_name,
            "modality": self.modality,
            "nominal_gsd_m": self.nominal_gsd_m,
            "bands": self.bands,
            "swath_km": self.swath_km,
            "polarization": self.polarization,
            "description": self.description,
        }


# Comprehensive Catalog of ISRO EO Missions
ISRO_SENSOR_CATALOG: Dict[str, ISROSensorProfile] = {
    "cartosat_3_pan": ISROSensorProfile(
        satellite_name="Cartosat-3",
        sensor_name="PAN (Panchromatic)",
        modality="optical",
        nominal_gsd_m=0.28,
        bands=["Panchromatic (0.45 - 0.90 µm)"],
        swath_km=17.0,
        description="ISRO 3rd-generation agile Earth observation satellite with 0.28m ground sampling distance.",
    ),
    "cartosat_3_mx": ISROSensorProfile(
        satellite_name="Cartosat-3",
        sensor_name="MX (Multi-Spectral 4-Band)",
        modality="multispectral",
        nominal_gsd_m=1.12,
        bands=["B2 (Blue)", "B3 (Green)", "B4 (Red)", "B5 (Near-Infrared)"],
        swath_km=17.0,
        description="Cartosat-3 Multi-Spectral 4-band radiometer at 1.12m resolution.",
    ),
    "cartosat_2": ISROSensorProfile(
        satellite_name="Cartosat-2 Series",
        sensor_name="PAN / MX",
        modality="optical",
        nominal_gsd_m=0.65,
        bands=["Panchromatic", "Visible-NIR 4-band"],
        swath_km=9.6,
        description="High-resolution cartographic satellite series providing 0.65m imagery.",
    ),
    "resourcesat_liss4": ISROSensorProfile(
        satellite_name="Resourcesat-2 / 2A",
        sensor_name="LISS-4 (Linear Imaging Self-Scanning Sensor)",
        modality="multispectral",
        nominal_gsd_m=5.8,
        bands=["B2 (Green: 0.52-0.59 µm)", "B3 (Red: 0.62-0.68 µm)", "B4 (NIR: 0.77-0.86 µm)"],
        swath_km=70.0,
        description="Multi-spectral high-resolution sensor for land use, crop monitoring, and urban planning.",
    ),
    "resourcesat_awifs": ISROSensorProfile(
        satellite_name="Resourcesat-2 / 2A",
        sensor_name="AWiFS (Advanced Wide Field Sensor)",
        modality="multispectral",
        nominal_gsd_m=56.0,
        bands=["B2 (Green)", "B3 (Red)", "B4 (NIR)", "B5 (SWIR: 1.55-1.70 µm)"],
        swath_km=740.0,
        description="Wide-swath synoptic sensor for regional vegetation monitoring and disaster management.",
    ),
    "risat_1_frs1": ISROSensorProfile(
        satellite_name="RISAT-1 / EOS-04",
        sensor_name="FRS-1 (Fine Resolution Stripmap-1)",
        modality="sar",
        nominal_gsd_m=1.0,
        bands=["C-band (5.35 GHz)"],
        swath_km=10.0,
        polarization=["HH", "HV", "VV", "VH", "Circular RH/RV (Hybrid Pol)"],
        description="All-weather, day-night C-band radar with 1.0m fine resolution and hybrid polarimetry.",
    ),
    "risat_1_mrs": ISROSensorProfile(
        satellite_name="RISAT-1 / EOS-04",
        sensor_name="MRS (Medium Resolution ScanSAR)",
        modality="sar",
        nominal_gsd_m=8.0,
        bands=["C-band (5.35 GHz)"],
        swath_km=115.0,
        polarization=["HH", "HV", "VV", "VH"],
        description="Medium resolution all-weather radar for soil moisture, flood mapping, and agriculture.",
    ),
    "oceansat_3_ocm": ISROSensorProfile(
        satellite_name="Oceansat-3 / EOS-06",
        sensor_name="OCM-3 (Ocean Color Monitor-3)",
        modality="multispectral",
        nominal_gsd_m=360.0,
        bands=["13 Spectral Bands (412 nm - 865 nm)"],
        swath_km=1420.0,
        description="High-sensitivity ocean color instrument for chlorophyll, sediment, and coastal zones.",
    ),
}


def detect_isro_sensor(identifier: str) -> Optional[ISROSensorProfile]:
    """Detect ISRO satellite and sensor type from filename, product code, or metadata string.
    
    Examples:
        - "C3_PAN_20240315_BANGALORE.tif" -> Cartosat-3 PAN (0.28m)
        - "RS2A_LISS4_STD_2023.tif" -> Resourcesat-2A LISS-4 (5.8m)
        - "EOS04_FRS1_HH_2024.tif" -> RISAT-1/EOS-04 FRS-1 (1.0m SAR)
    """
    id_clean = identifier.upper().replace("-", "_").replace(" ", "_")

    if re.search(r"CARTOSAT_?3.*PAN|C3_?PAN", id_clean):
        return ISRO_SENSOR_CATALOG["cartosat_3_pan"]
    elif re.search(r"CARTOSAT_?3|C3_?MX", id_clean):
        return ISRO_SENSOR_CATALOG["cartosat_3_mx"]
    elif re.search(r"CARTOSAT_?2|C2", id_clean):
        return ISRO_SENSOR_CATALOG["cartosat_2"]
    elif re.search(r"LISS_?4|LISS4|RS2.*LISS", id_clean):
        return ISRO_SENSOR_CATALOG["resourcesat_liss4"]
    elif re.search(r"AWIFS|RS2.*AWIFS", id_clean):
        return ISRO_SENSOR_CATALOG["resourcesat_awifs"]
    elif re.search(r"RISAT_?1.*FRS|EOS_?04.*FRS|FRS_?1", id_clean):
        return ISRO_SENSOR_CATALOG["risat_1_frs1"]
    elif re.search(r"RISAT_?1|EOS_?04|RISAT", id_clean):
        return ISRO_SENSOR_CATALOG["risat_1_mrs"]
    elif re.search(r"OCEANSAT|OCM_?3|EOS_?06", id_clean):
        return ISRO_SENSOR_CATALOG["oceansat_3_ocm"]

    return None


def get_isro_sensor_catalog() -> List[Dict[str, Any]]:
    """Return list of all supported ISRO satellite sensor profiles."""
    return [p.to_dict() for p in ISRO_SENSOR_CATALOG.values()]
