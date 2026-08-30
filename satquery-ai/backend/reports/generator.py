"""Multi-format audit report generator for SatQuery AI (PDF, GeoJSON, CSV)."""

import io
import csv
import json
from typing import Dict, Any, Optional
from ..models_db import AnalysisJob

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:  # pragma: no cover
    HAS_REPORTLAB = False


def generate_pdf_report(job: AnalysisJob) -> bytes:
    """Generate a formatted PDF mission audit report."""
    buf = io.BytesIO()
    res = job.result or {}
    confidence_val = job.confidence or 0.0

    if HAS_REPORTLAB:
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        story.append(Paragraph("SatQuery AI — Remote Sensing Analysis Dossier", title_style))
        story.append(Spacer(1, 10))

        # Metadata Header Table
        meta_data = [
            ["Job ID:", job.id, "Timestamp:", str(job.created_at or "")],
            ["Task Type:", job.task.upper(), "Status:", job.status.upper()],
            ["Confidence:", f"{int(confidence_val * 100)}%", "AOI ID:", str(job.aoi_id or "Global/Direct")],
        ]
        meta_table = Table(meta_data, colWidths=[90, 170, 90, 170])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Question & Answer
        story.append(Paragraph("<b>Natural-Language Query:</b>", styles["Normal"]))
        story.append(Paragraph(f"<i>{job.question or 'N/A'}</i>", styles["Normal"]))
        story.append(Spacer(1, 10))

        claim_text = res.get("joint_claim") or res.get("answer") or json.dumps(res, indent=2)
        story.append(Paragraph("<b>Grounded Result & Findings:</b>", styles["Normal"]))
        story.append(Paragraph(f"{claim_text}", styles["Normal"]))
        story.append(Spacer(1, 14))

        # Quantified Metrics if present
        if "change_percent" in res:
            story.append(Paragraph("<b>Quantified Change Metrics:</b>", styles["Heading3"]))
            cd_data = [
                ["Metric", "Value"],
                ["Surface Alteration", f"{res.get('change_percent')}%"],
                ["Total Area Changed", f"{res.get('total_area_m2', 0):,.1f} m²"],
                ["Ground Extent (ha)", f"{res.get('total_area_ha', 0)} ha"],
                ["Distinct Clusters", str(res.get("cluster_count", 0))],
            ]
            t = Table(cd_data, colWidths=[200, 320])
            t.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ])
            )
            story.append(t)
            story.append(Spacer(1, 14))

        doc.build(story)
        return buf.getvalue()
    else:
        # Fallback minimal plain text PDF stream
        content = f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n200\n%%EOF"
        return content.encode("utf-8")


def generate_geojson_report(job: AnalysisJob) -> Dict[str, Any]:
    """Extract and format GeoJSON features associated with an analysis job."""
    res = job.result or {}
    fc = res.get("feature_collection") or res.get("regions_geojson")
    if fc and isinstance(fc, dict):
        return fc
    return {
        "type": "FeatureCollection",
        "features": [],
        "properties": {
            "job_id": job.id,
            "task": job.task,
            "status": job.status,
        },
    }


def generate_csv_report(job: AnalysisJob) -> str:
    """Generate tabular CSV report summarizing analysis metrics and clusters."""
    res = job.result or {}
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Analysis Job Report", "SatQuery AI"])
    writer.writerow(["Job ID", job.id])
    writer.writerow(["Task", job.task])
    writer.writerow(["Status", job.status])
    writer.writerow(["Confidence", job.confidence])
    writer.writerow(["Question", job.question])
    writer.writerow([])

    fc = res.get("feature_collection") or res.get("regions_geojson")
    if fc and isinstance(fc, dict) and "features" in fc:
        writer.writerow(["Feature ID", "Area (m²)", "Area (ha)", "Cluster ID / Label"])
        for feat in fc["features"]:
            props = feat.get("properties", {})
            writer.writerow([
                feat.get("id", "N/A"),
                props.get("area_m2", 0),
                props.get("area_ha", 0),
                props.get("cluster_id") or props.get("label", "N/A"),
            ])
    else:
        writer.writerow(["Key", "Value"])
        for k, v in res.items():
            if isinstance(v, (int, float, str, bool)):
                writer.writerow([k, v])

    return output.getvalue()
