"""Unit tests for ISRO satellite product metadata resolvers and sensor catalog."""

import pytest
from backend.geospatial.isro_formats import (
    detect_isro_sensor,
    get_isro_sensor_catalog,
    ISROSensorProfile,
    ISRO_SENSOR_CATALOG,
)


def test_isro_sensor_catalog_integrity():
    catalog = get_isro_sensor_catalog()
    assert len(catalog) >= 6

    # Verify Cartosat-3 entry
    c3 = ISRO_SENSOR_CATALOG["cartosat_3_pan"]
    assert isinstance(c3, ISROSensorProfile)
    assert c3.nominal_gsd_m == 0.28
    assert c3.modality == "optical"

    # Verify RISAT-1 entry
    risat = ISRO_SENSOR_CATALOG["risat_1_frs1"]
    assert risat.modality == "sar"
    assert risat.nominal_gsd_m == 1.0
    assert "HH" in (risat.polarization or [])


def test_detect_isro_sensor_patterns():
    # Cartosat-3 PAN
    s1 = detect_isro_sensor("C3_PAN_20240315_BANGALORE.tif")
    assert s1 is not None
    assert s1.satellite_name == "Cartosat-3"
    assert s1.nominal_gsd_m == 0.28

    # Resourcesat-2A LISS-4
    s2 = detect_isro_sensor("RS2A_LISS4_STANDARD_SCENE.tif")
    assert s2 is not None
    assert s2.sensor_name.startswith("LISS-4")
    assert s2.nominal_gsd_m == 5.8

    # RISAT-1 / EOS-04 FRS
    s3 = detect_isro_sensor("EOS04_FRS1_HH_2023.tif")
    assert s3 is not None
    assert s3.modality == "sar"

    # Unrecognized returns None safely
    s_unknown = detect_isro_sensor("random_landsat_8.tif")
    assert s_unknown is None
