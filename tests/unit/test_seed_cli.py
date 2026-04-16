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


def test_legacy_bench_emits_deprecation(monkeypatch):
    import importlib
    import sys
    import warnings

    # Force fresh import to trigger the top-level deprecation warning.
    for m in list(sys.modules):
        if m.startswith("seed_dsi_bench") or m == "_seed_dsi_bench_legacy":
            del sys.modules[m]

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        try:
            from seed import bench
            # Importing the module will not yet trigger the legacy import;
            # call _load_legacy explicitly.
            bench._load_legacy()
        except Exception:
            # Legacy seed has heavy DB imports; we only care the
            # deprecation warning fires first.
            pass
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "python -m seed bench" in str(w.message)
        for w in captured
    ), f"expected DeprecationWarning from seed_dsi_bench import, got {captured}"
