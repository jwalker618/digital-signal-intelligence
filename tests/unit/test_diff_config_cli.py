"""Tests for the V6/C7 `diff-config` CLI subcommand."""
from __future__ import annotations

import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_diff(tmp_path: Path, base_text: str | None, head_text: str, coverage: str) -> tuple[int, str]:
    base_path = tmp_path / "base.yaml"
    head_path = tmp_path / "head.yaml"
    if base_text is not None:
        base_path.write_text(base_text)
    head_path.write_text(head_text)

    out_path = tmp_path / "out.md"
    result = subprocess.run(
        [
            sys.executable, "-m", "infrastructure.builder.cli", "diff-config",
            "--base-file", str(base_path) if base_text is not None else "/does/not/exist",
            "--head-file", str(head_path),
            "--coverage", coverage,
            "--output", str(out_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True, text=True,
    )
    output = out_path.read_text() if out_path.exists() else result.stdout
    return result.returncode, output


def test_identical_configs_report_no_change(tmp_path: Path):
    base_text = (REPO_ROOT / "coverages" / "cyber" / "config.yaml").read_text()
    head_text = base_text

    code, out = _run_diff(tmp_path, base_text, head_text, "cyber")

    assert code == 0
    assert "logic.md diff" in out
    assert "No change" in out


def test_description_change_surfaces_in_diff(tmp_path: Path):
    base_text = (REPO_ROOT / "coverages" / "cyber" / "config.yaml").read_text()
    # Replace the first description line with a marker string.
    head_text = base_text.replace(
        "Cyber liability model based on externally observable technical",
        "DSIV6TESTCHANGE marker",
        1,
    )
    assert head_text != base_text, "sed-equivalent replacement failed"

    code, out = _run_diff(tmp_path, base_text, head_text, "cyber")

    assert code == 0
    assert "```diff" in out
    assert "DSIV6TESTCHANGE" in out


def test_missing_base_file_treated_as_empty(tmp_path: Path):
    """If a config file is new in the PR (no base), the diff renders as an addition."""
    head_text = (REPO_ROOT / "coverages" / "cyber" / "config.yaml").read_text()

    code, out = _run_diff(tmp_path, None, head_text, "cyber")

    assert code == 0
    assert "```diff" in out
    assert "+## Model:" in out or "logic.md diff" in out
