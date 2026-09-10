"""Unit tests for PDF, GeoJSON, and CSV report generator."""

from backend.models_db import AnalysisJob
from backend.reports.generator import (
    generate_pdf_report,
    generate_geojson_report,
    generate_csv_report,
)


def test_report_generation():
    dummy_job = AnalysisJob(
        id="job_test_123",
        aoi_id="aoi_test",
        task="bi_temporal_change",
        status="completed",
        question="What changed between these dates?",
        confidence=0.92,
        result={
            "change_percent": 12.5,
            "total_area_m2": 150000.0,
            "total_area_ha": 15.0,
            "cluster_count": 3,
            "joint_claim": "Detected 12.5% alteration across 15.0 ha.",
            "feature_collection": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "change_1",
                        "properties": {"area_m2": 50000.0, "area_ha": 5.0, "cluster_id": 1},
                        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    }
                ],
            },
        },
    )

    # 1. Test PDF
    pdf_bytes = generate_pdf_report(dummy_job)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")

    # 2. Test GeoJSON
    geojson_dict = generate_geojson_report(dummy_job)
    assert geojson_dict["type"] == "FeatureCollection"
    assert len(geojson_dict["features"]) == 1

    # 3. Test CSV
    csv_str = generate_csv_report(dummy_job)
    assert "Job ID,job_test_123" in csv_str
    assert "change_1" in csv_str
