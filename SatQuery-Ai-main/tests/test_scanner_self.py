import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from backend.evidence.truthlock_scanner import scan_file


def _write(tmpdir: Path, name: str, content: str) -> Path:
    p = tmpdir / name
    p.write_text(content)
    return p


def test_flags_real_hardcoded_confidence():
    with tempfile.TemporaryDirectory() as d:
        p = _write(Path(d), "bad.py", 'result = {"confidence": 0.9400}\n')
        violations = scan_file(p)
        assert any(v.rule == "hardcoded_confidence" for v in violations)


def test_does_not_flag_docstring_example():
    with tempfile.TemporaryDirectory() as d:
        content = (
            '"""\n'
            'Bad pattern to avoid: confidence: 0.9400\n'
            '"""\n'
            "def f():\n"
            "    return 1\n"
        )
        p = _write(Path(d), "documented.py", content)
        violations = scan_file(p)
        assert violations == []


def test_does_not_flag_line_comment():
    with tempfile.TemporaryDirectory() as d:
        content = "# never do: confidence: 0.9400\ndef f():\n    return 1\n"
        p = _write(Path(d), "commented.py", content)
        violations = scan_file(p)
        assert violations == []


def test_suppression_marker_overrides_real_code_line():
    with tempfile.TemporaryDirectory() as d:
        content = 'x = {"confidence": 0.9400}  # truthlock:allow -- reviewed exception\n'
        p = _write(Path(d), "suppressed.py", content)
        violations = scan_file(p)
        assert violations == []


def test_ts_block_comment_not_flagged():
    with tempfile.TemporaryDirectory() as d:
        content = (
            "/*\n"
            " * example: confidence: 0.9400 is forbidden\n"
            " */\n"
            "const x = 1;\n"
        )
        p = _write(Path(d), "documented.ts", content)
        violations = scan_file(p)
        assert violations == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
