"""V6/E1 — rust_bindings shim tests.

Validates the runtime-selection contract: flag + import-failure
fallback. The actual parity-vs-Python check lives in the nightly
`rust-parity` CI job once the Rust module is compiled.
"""
from __future__ import annotations

import importlib


def test_rust_enabled_flag_parses(monkeypatch):
    from signal_architecture.signals import rust_bindings
    importlib.reload(rust_bindings)
    monkeypatch.setenv("DSI_USE_RUST_SCORER", "true")
    assert rust_bindings._rust_enabled() is True
    monkeypatch.setenv("DSI_USE_RUST_SCORER", "0")
    assert rust_bindings._rust_enabled() is False
    monkeypatch.delenv("DSI_USE_RUST_SCORER", raising=False)
    assert rust_bindings._rust_enabled() is False


def test_try_import_rust_returns_none_when_missing(monkeypatch):
    import sys
    from signal_architecture.signals import rust_bindings
    # Ensure dsi_core is not importable in the test env.
    assert "dsi_core" not in sys.modules
    assert rust_bindings._try_import_rust() is None


def test_score_falls_back_to_python_without_rust(monkeypatch):
    """When rust is unavailable or disabled, score() delegates to Python."""
    from signal_architecture.signals import rust_bindings

    called = {}

    def fake_py_score(*, config_hash, signals):
        called["args"] = (config_hash, list(signals))
        return "py-result"

    # Monkeypatch at import site.
    import layers.risk.scorer as py_scorer
    monkeypatch.setattr(py_scorer, "score", fake_py_score, raising=False)

    result = rust_bindings.score("hash-x", [1, 2, 3], use_rust=False)
    assert result == "py-result"
    assert called["args"][0] == "hash-x"
    assert called["args"][1] == [1, 2, 3]
