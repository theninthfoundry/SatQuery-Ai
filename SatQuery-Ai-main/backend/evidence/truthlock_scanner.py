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
        re.compile(r"\bconfidence[\"'`]?\s*[:=]\s*0\.\d{2,4}\b", re.IGNORECASE),
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

ALLOWED_PATH_SUBSTRINGS = (
    "fixtures/", "/tests/", "test_", "/docs/", ".md",
    "truthlock_scanner.py",  # the scanner's own pattern/reason strings are not violations
)
SCAN_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}

# Inline escape hatch for a line that is deliberately documenting an
# anti-pattern (e.g. "never write model_name='changenet' without a status
# check") rather than committing it. Deliberately loud and greppable so
# it can't be used silently to launder a real violation.
SUPPRESSION_MARKER = "truthlock:allow"

# A line is treated as non-executable documentation (comment or inside a
# docstring/comment block) if it matches one of these — false positives
# inside comments/docstrings are noise that trains people to ignore the
# scanner, which defeats its purpose as a hard CI gate.
_LINE_COMMENT_PREFIXES = ("#", "//", "*", '"""', "'''")


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


def _mask_non_code_lines(lines: list[str], suffix: str) -> list[bool]:
    """
    Returns a per-line boolean: True if the line is real, executable
    code (should be scanned), False if it's inside a comment or
    docstring block (documentation, exempt from the pattern scan).

    Handles Python triple-quoted docstrings, // line comments, and /* */
    block comments (TS/JS). This is intentionally simple — a full
    tokenizer isn't needed to solve "don't flag documentation."
    """
    is_code = [True] * len(lines)
    in_py_docstring = False
    py_docstring_delim = None
    in_block_comment = False

    for i, raw in enumerate(lines):
        stripped = raw.strip()

        if suffix == ".py":
            if in_py_docstring:
                is_code[i] = False
                if py_docstring_delim in raw:
                    in_py_docstring = False
                continue
            for delim in ('"""', "'''"):
                if stripped.startswith(delim):
                    is_code[i] = False
                    # single-line docstring like """foo""" doesn't open a block
                    if stripped.count(delim) < 2:
                        in_py_docstring = True
                        py_docstring_delim = delim
                    break
            else:
                if stripped.startswith("#"):
                    is_code[i] = False
        else:  # ts/tsx/js/jsx
            if in_block_comment:
                is_code[i] = False
                if "*/" in raw:
                    in_block_comment = False
                continue
            if stripped.startswith("//") or stripped.startswith("*"):
                is_code[i] = False
            elif stripped.startswith("/*"):
                is_code[i] = False
                if "*/" not in raw:
                    in_block_comment = True

    return is_code


def scan_file(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations

    lines = text.splitlines()
    is_code = _mask_non_code_lines(lines, path.suffix)

    for name, pattern, reason in PATTERNS:
        for m in pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
            if not is_code[line_no - 1]:
                continue  # documentation/comment describing the anti-pattern, not committing it
            if SUPPRESSION_MARKER in line:
                continue  # explicit, greppable, human-reviewed exception
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
