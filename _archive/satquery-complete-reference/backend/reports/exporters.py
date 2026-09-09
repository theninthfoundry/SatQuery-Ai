"""
backend/reports/exporters.py

Turns an EvidenceContract dict into the three downloadable formats the
Mission Workspace UI offers: GeoJSON (for GIS tools), CSV (for
spreadsheets/quick review), and a PDF mission dossier (for reporting to
non-technical stakeholders). All three read only from the evidence dict
-- no re-computation, so exports can never disagree with what the UI
displayed.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Optional

from backend.config.settings import REPORTS_OUT_DIR


def export_geojson(evidence: dict, out_path: Optional[str] = None) -> str:
    fc = evidence.get("spatial_evidence") or {"type": "FeatureCollection", "features": []}
    out_path = out_path or str(REPORTS_OUT_DIR / f"{evidence['id']}.geojson")
    Path(out_path).write_text(json.dumps(fc, indent=2))
    return out_path


def export_csv(evidence: dict, out_path: Optional[str] = None) -> str:
    out_path = out_path or str(REPORTS_OUT_DIR / f"{evidence['id']}.csv")
    fc = evidence.get("spatial_evidence") or {"features": []}
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["evidence_id", "task", "model", "is_real_weights", "fallback_used",
                      "reliability_score"])
    writer.writerow([evidence["id"], evidence["task"], evidence["model"],
                      evidence["is_real_weights"], evidence["fallback_used"],
                      evidence["reliability_score"]])
    writer.writerow([])
    writer.writerow(["metric", "value"])
    for k, v in evidence.get("metrics", {}).items():
        writer.writerow([k, v])
    if fc.get("features"):
        writer.writerow([])
        writer.writerow(["feature_index", "properties"])
        for i, feat in enumerate(fc["features"]):
            writer.writerow([i, json.dumps(feat.get("properties", {}))])
    Path(out_path).write_text(buf.getvalue())
    return out_path


def export_pdf_dossier(evidence: dict, routing_summary: Optional[dict] = None,
                        out_path: Optional[str] = None) -> str:
    """Builds a mission dossier PDF using reportlab if available, else
    falls back to a well-formatted plain-text .txt dossier so export
    never silently fails on a missing optional dependency."""
    out_path = out_path or str(REPORTS_OUT_DIR / f"{evidence['id']}_dossier.pdf")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        y = height - 25 * mm

        def line(text, size=10, dy=6 * mm, bold=False):
            nonlocal y
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(20 * mm, y, text[:110])
            y -= dy

        line("SatQuery AI -- Mission Evidence Dossier", size=16, bold=True, dy=10 * mm)
        line(f"Evidence ID: {evidence['id']}")
        line(f"Task: {evidence['task']}")
        line(f"Model: {evidence['model']}")
        line(f"Real weights: {evidence['is_real_weights']}   Fallback used: {evidence['fallback_used']}")
        line(f"Reliability score: {evidence['reliability_score']}")
        y -= 4 * mm
        line("Claim:", bold=True)
        for chunk in _wrap(evidence["claim"], 95):
            line(chunk)
        y -= 4 * mm
        line("Metrics:", bold=True)
        for k, v in evidence.get("metrics", {}).items():
            line(f"  {k}: {v}")
        if evidence.get("warnings"):
            y -= 4 * mm
            line("Warnings:", bold=True)
            for w in evidence["warnings"]:
                for chunk in _wrap(w, 95):
                    line(f"  {chunk}")
        y -= 4 * mm
        line("Provenance trace:", bold=True)
        for step in evidence.get("provenance_steps", []):
            line(f"  [{step['step']}] {step['tool']} -- {step['duration_ms']}ms")
        if routing_summary:
            y -= 4 * mm
            line("Routing:", bold=True)
            line(f"  tool_selected: {routing_summary.get('tool_selected')}")
        c.showPage()
        c.save()
        return out_path
    except ImportError:
        return _export_text_dossier(evidence, routing_summary, out_path.replace(".pdf", ".txt"))


def _export_text_dossier(evidence: dict, routing_summary: Optional[dict], out_path: str) -> str:
    lines = [
        "SatQuery AI -- Mission Evidence Dossier (reportlab not installed; plain-text fallback)",
        "=" * 78,
        f"Evidence ID: {evidence['id']}",
        f"Task: {evidence['task']}",
        f"Model: {evidence['model']}",
        f"Real weights: {evidence['is_real_weights']}   Fallback used: {evidence['fallback_used']}",
        f"Reliability score: {evidence['reliability_score']}",
        "",
        "Claim:",
        f"  {evidence['claim']}",
        "",
        "Metrics:",
    ]
    for k, v in evidence.get("metrics", {}).items():
        lines.append(f"  {k}: {v}")
    if evidence.get("warnings"):
        lines.append("")
        lines.append("Warnings:")
        for w in evidence["warnings"]:
            lines.append(f"  - {w}")
    lines.append("")
    lines.append("Provenance trace:")
    for step in evidence.get("provenance_steps", []):
        lines.append(f"  [{step['step']}] {step['tool']} -- {step['duration_ms']}ms")
    Path(out_path).write_text("\n".join(lines))
    return out_path


def _wrap(text: str, width: int) -> list:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines

