"""Smoke tests for the V6/C4 seed CLI skeleton.

These tests exercise argparse wiring + the thin-wrapper dispatch paths
without actually touching a database. The legacy scripts emit
DeprecationWarning on import, which the bench/v5 wrappers trigger.
"""
from __future__ import annotations

import pytest


def test_cli_parser_exposes_all_commands():
    from seed.cli import _build_parser
    parser = _build_parser()
    # argparse stores subparsers in a choices dict on the subparser action.
    sub_action = next(
        a for a in parser._subparsers._group_actions
        if getattr(a, "choices", None)
    )
    cmds = set(sub_action.choices.keys())
    assert cmds == {"init", "bench", "v5", "synthetic", "reset", "verify"}


def test_reset_without_confirm_refuses():
    from seed import reset
    assert reset.run(confirm=False) == 2


def test_reset_with_confirm_placeholder():
    from seed import reset
    # C4-interim returns 0 and prints guidance — verified in follow-up.
    assert reset.run(confirm=True) == 0


def test_legacy_scripts_removed_from_repo_root():
    """V6/C4-final deleted the legacy scripts from the repo root."""
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    assert not (repo_root / "seed_dsi_bench.py").exists()
    assert not (repo_root / "seed_v5.py").exists()
    assert not (repo_root / "synthetic_generator.py").exists()


def test_seed_bench_exposes_run_callable():
    from seed import bench
    assert callable(getattr(bench, "run", None))


def test_seed_v5_exposes_run_callable():
    from seed import v5
    assert callable(getattr(v5, "run", None))


def test_seed_synthetic_exposes_run_callable():
    from seed import synthetic
    assert callable(getattr(synthetic, "run", None))
