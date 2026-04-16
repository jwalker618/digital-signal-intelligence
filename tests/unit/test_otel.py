"""Smoke tests for V6/C3 OpenTelemetry bootstrap."""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def otel_module():
    from infrastructure.api.observability import otel
    importlib.reload(otel)
    return otel


def test_noop_when_disabled(monkeypatch, otel_module):
    monkeypatch.delenv("DSI_OTEL_ENABLED", raising=False)
    assert otel_module.is_enabled() is False
    # Safe no-op even without app/engine
    otel_module.init_otel()
    # extractor_span yields None so callers don't need to branch
    with otel_module.extractor_span("my_source", entity_id="e1") as span:
        assert span is None


def test_enabled_flag_bool_parsing(monkeypatch, otel_module):
    monkeypatch.setenv("DSI_OTEL_ENABLED", "true")
    assert otel_module.is_enabled() is True
    monkeypatch.setenv("DSI_OTEL_ENABLED", "YES")
    assert otel_module.is_enabled() is True
    monkeypatch.setenv("DSI_OTEL_ENABLED", "off")
    assert otel_module.is_enabled() is False
    monkeypatch.setenv("DSI_OTEL_ENABLED", "0")
    assert otel_module.is_enabled() is False


def test_extractor_span_never_raises_when_uninitialised(otel_module):
    # Even inside the context manager, missing OTel package must not crash.
    try:
        with otel_module.extractor_span(
            "paid_source",
            entity_id="e1",
            coverage="cyber",
            config_name="cyber_general",
            cost_tier="paid",
            cache_hit=False,
        ) as _:
            pass
    except Exception as e:
        pytest.fail(f"extractor_span raised when uninitialised: {e}")
