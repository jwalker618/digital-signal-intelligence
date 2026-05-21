"""V7 Phase 2 — meta-test of the evidence-completeness linter.

We construct two synthetic Python files in a tmpdir — one violating
(missing evidence_grade), one clean (has evidence_grade) — and assert
the linter flags exactly the violator.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Locate the module under test from scripts/ — it lives outside the package tree.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import lint_evidence_completeness as lint  # type: ignore  # noqa: E402


VIOLATING = """\
from signal_architecture.signals.types import SignalResult


def bad():
    return SignalResult(signal_id="x", score=50.0, confidence=0.5)
"""

CLEAN = """\
from signal_architecture.signals.types import SignalResult


def good():
    return SignalResult(
        signal_id="x",
        score=50.0,
        confidence=0.5,
        evidence_grade="inferred",
        evidence_basis="stub",
        evidence_sources=[],
    )
"""

ERROR_ONLY = """\
from signal_architecture.signals.types import SignalResult


def err():
    return SignalResult(signal_id="x", error="fetch failed")
"""

SKIPPED_ONLY = """\
from signal_architecture.signals.types import SignalResult


def skip():
    return SignalResult(signal_id="x", skipped=True)
"""


def test_violator_flagged(tmp_path: Path):
    p = tmp_path / "bad.py"
    p.write_text(VIOLATING, encoding="utf-8")
    violations = lint.violations_in(p)
    assert len(violations) == 1
    assert violations[0][1] == "missing evidence_grade kwarg"


def test_clean_passes(tmp_path: Path):
    p = tmp_path / "good.py"
    p.write_text(CLEAN, encoding="utf-8")
    assert lint.violations_in(p) == []


def test_error_only_passes(tmp_path: Path):
    p = tmp_path / "err.py"
    p.write_text(ERROR_ONLY, encoding="utf-8")
    assert lint.violations_in(p) == []


def test_skipped_only_passes(tmp_path: Path):
    p = tmp_path / "skip.py"
    p.write_text(SKIPPED_ONLY, encoding="utf-8")
    assert lint.violations_in(p) == []


def test_attribute_access_recognised(tmp_path: Path):
    """`signals.SignalResult(...)` is the same construction; linter must catch it."""
    p = tmp_path / "attr.py"
    p.write_text(
        "import signal_architecture.signals as s\n"
        "x = s.SignalResult(signal_id='x', score=1, confidence=1)\n",
        encoding="utf-8",
    )
    violations = lint.violations_in(p)
    assert len(violations) == 1
