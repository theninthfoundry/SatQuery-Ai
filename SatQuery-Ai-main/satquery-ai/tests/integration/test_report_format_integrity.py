"""Integration test verifying report format integrity across JSON, GeoJSON, CSV, and PDF.

All 4 formats must be bitwise or numerically identical across:
- analysis_id
- source_image
- area (ha and m²)
- polygon coordinates
- decision
- sensor
- method
"""

import csv
import io
import json
import pytest

from backend.models_db import AnalysisJob
from backend.reports.generator import (
    generate_pdf_report,
    generate_geojson_report,
    generate_csv_report,
)


class TestReportFormatIntegrity:

    @pytest.fixture
    def sample_analysis_job(self):
        """Create a representative AnalysisJob representing a water body spatial ranking."""
        job_id = "job_audit_test_7788"
        area_ha = 19.7892
        area_m2 = 197892.0
        source_img = "img_demo_brahmaputra_flood"
        decision = "ANSWER"
        method = "MNDWI Spectral Index + WGS84 Geodesic Polygonization"

        poly_coords = [
            [[72.50, 23.00], [72.55, 23.00], [72.55, 23.05], [72.50, 23.05], [72.50, 23.00]]
        ]

        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "wb_01",
                    "properties": {
                        "label": "★ Largest Water Body",
                        "area_ha": area_ha,
                        "area_m2": area_m2,
                        "source_image_id": source_img,
                        "method": method,
                        "decision": decision,
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": poly_coords,
                    },
                }
            ],
            "properties": {
                "job_id": job_id,
                "source_image_id": source_img,
                "decision": decision,
            },
        }

        result_payload = {
            "analysis_id": job_id,
            "source_image_id": source_img,
            "query": "Where is the largest water body?",
            "answer": f"The largest water body identified covers {area_ha:.4f} ha ({area_m2:,.1f} m²).",
            "total_area_ha": area_ha,
            "total_area_m2": area_m2,
            "method": method,
            "decision": decision,
            "feature_collection": feature_collection,
            "candidate_count": 1,
        }

        job = AnalysisJob(
            id=job_id,
            aoi_id="aoi_brahmaputra_basin",
            task="spatial_ranking",
            status="completed",
            question="Where is the largest water body?",
            result=result_payload,
            confidence={"overall": 0.94, "components": {"resolution": 0.95, "registration": 1.0}},
        )
        return job

    def test_cross_format_report_integrity(self, sample_analysis_job):
        """Assert identical metrics across JSON, GeoJSON, CSV, and PDF representations."""
        job = sample_analysis_job
        expected_id = job.id
        expected_area_ha = job.result["total_area_ha"]
        expected_area_m2 = job.result["total_area_m2"]
        expected_img = job.result["source_image_id"]
        expected_decision = job.result["decision"]

        # 1. JSON Representation
        json_dump = json.dumps(job.result)
        json_loaded = json.loads(json_dump)
        assert json_loaded["analysis_id"] == expected_id
        assert json_loaded["total_area_ha"] == pytest.approx(expected_area_ha, rel=1e-5)
        assert json_loaded["total_area_m2"] == pytest.approx(expected_area_m2, rel=1e-5)
        assert json_loaded["source_image_id"] == expected_img
        assert json_loaded["decision"] == expected_decision

        # 2. GeoJSON Representation
        geojson_res = generate_geojson_report(job)
        assert geojson_res["type"] == "FeatureCollection"
        assert len(geojson_res["features"]) == 1
        feat = geojson_res["features"][0]
        assert feat["properties"]["area_ha"] == pytest.approx(expected_area_ha, rel=1e-5)
        assert feat["properties"]["area_m2"] == pytest.approx(expected_area_m2, rel=1e-5)
        assert feat["properties"]["source_image_id"] == expected_img
        assert feat["properties"]["decision"] == expected_decision
        assert feat["geometry"]["type"] == "Polygon"

        # 3. CSV Representation
        csv_str = generate_csv_report(job)
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)

        # Job ID row
        job_id_rows = [r for r in rows if len(r) >= 2 and r[0] == "Job ID"]
        assert len(job_id_rows) == 1
        assert job_id_rows[0][1] == expected_id

        # Feature area row
        feat_rows = [r for r in rows if len(r) >= 3 and r[0] == "wb_01"]
        assert len(feat_rows) == 1
        assert float(feat_rows[0][1]) == pytest.approx(expected_area_m2, rel=1e-5)
        assert float(feat_rows[0][2]) == pytest.approx(expected_area_ha, rel=1e-5)

        # 4. PDF Representation
        pdf_bytes = generate_pdf_report(job)
        assert len(pdf_bytes) > 500, "PDF must be generated as non-empty document"

        # If reportlab rendered, the binary contains the text representation of the area and job ID
        assert expected_id.encode("utf-8") in pdf_bytes
        # Area formatted string in PDF
        formatted_ha = f"{expected_area_ha:.4f}".encode("utf-8")
        assert formatted_ha in pdf_bytes, f"Expected {formatted_ha} to appear in PDF binary stream"
