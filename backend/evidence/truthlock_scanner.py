#!/usr/bin/env python3
"""
TruthLock static scanner (audit section 46).

Scans result-generating code for patterns that indicate hardcoded /
synthetic values masquerading as real analysis output: fixed confidence
scores, hardcoded coordinates, fixed area/measurement numbers, hardcoded
dates, hardcoded SAR dB values, and named-but-unverified model strings.

Usage:
    python -m backend.evidence.truthlock_scanner backend/ apps/web/src/

Exit code is non-zero if any violation is found outside an allowed path
(fixtures/, tests/, docs/, *.md), which is exactly what should be wired
into CI as a hard FAIL, not a warning (audit section 45).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Each pattern: (name, compiled regex, why it's suspicious)
PATTERNS: list[tuple[str, re.Pattern, str]] = [
    (
        "hardcoded_confidence",
        re.compile(r"\bconfidence\s*[:=]\s*0\.\d{2,4}\b", re.IGNORECASE),
        "Fixed numeric confidence assigned directly rather than computed "
        "from EvidenceFactors.",
    ),
    (
        "platt_calibration_claim",
        re.compile(r"platt[-_ ]?calibrat", re.IGNORECASE),
        "Claims Platt calibration; only allowed if real calibration data "
        "and a fitted calibrator are present.",
    ),
    (
        "hardcoded_coordinate_pair",
        re.compile(r"-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}"),
        "Looks like a hardcoded lat/lon pair embedded in logic rather "
        "than sourced from real geometry.",
    ),
    (
        "hardcoded_area_ha",
        re.compile(r"\b\d+(\.\d+)?\s*ha\b", re.IGNORECASE),
        "Hardcoded hectare value; areas must come from Shapely geodesic "
        "computation, never a literal.",
    ),
    (
        "hardcoded_sar_db",
        re.compile(r"-?\d{1,2}(\.\d+)?\s*dB\b"),
        "Hardcoded SAR backscatter dB value; must come from real sigma0 "
        "computation.",
    ),
    (
        "hardcoded_gsd",
        re.compile(r"\b(10|20|60)\s*m\b(?!\w)"),
        "Hardcoded ground sample distance; must come from the "
        "ObservationRecord.gsd of the actual asset read.",
    ),
    (
        "named_model_without_status_check",
        re.compile(r"\b(ChangeNet(-V\d+)?|GeoChat|DOFA)\b(?!.{0,120}(READY|VERIFIED|assert_ready|is_ready))",
                    re.IGNORECASE | re.DOTALL),
        "Model name referenced without a nearby READY/VERIFIED status "
        "check — risk of implying real inference occurred.",
    ),
    (
        "iso_date_literal",
        re.compile(r"\b20\d{2}-\d{2}-\d{2}\b"),
        "Literal ISO date; timestamps must come from "
        "ObservationRecord.timestamp, not a string literal.",
    ),
]

ALLOWED_PATH_SUBSTRINGS = ("fixtures/", "/tests/", "test_", "/docs/", ".md")
SCAN_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}


@dataclass
class Violation:
    path: Path
    line_no: int
    line: str
    rule: str
    reason: str


def is_allowed_path(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    return any(sub in s for sub in ALLOWED_PATH_SUBSTRINGS)


def scan_file(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations

    for name, pattern, reason in PATTERNS:
        for m in pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line = text.splitlines()[line_no - 1].strip()
            violations.append(Violation(path, line_no, line, name, reason))
    return violations


def scan_paths(roots: list[str]) -> list[Violation]:
    all_violations: list[Violation] = []
    for root_str in roots:
        root = Path(root_str)
        if root.is_file():
            candidates = [root]
        else:
            candidates = [p for p in root.rglob("*") if p.suffix in SCAN_EXTENSIONS]
        for path in candidates:
            if is_allowed_path(path):
                continue
            all_violations.extend(scan_file(path))
    return all_violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TruthLock static scanner")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    violations = scan_paths(args.paths)

    if args.json:
        import json
        print(json.dumps(
            [
                {
                    "path": str(v.path),
                    "line_no": v.line_no,
                    "line": v.line,
                    "rule": v.rule,
                    "reason": v.reason,
                }
                for v in violations
            ],
            indent=2,
        ))
    else:
        for v in violations:
            print(f"{v.path}:{v.line_no}  [{v.rule}]  {v.line}")
            print(f"    -> {v.reason}\n")
        print(f"{len(violations)} violation(s) found.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
