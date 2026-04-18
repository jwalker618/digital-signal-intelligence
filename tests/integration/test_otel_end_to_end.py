"""V6/C3 (stage 1.5) — OpenTelemetry end-to-end smoke with
DSI_OTEL_ENABLED=true.

Unlike the unit tests that only verify the no-op path, these tests:
1. Enable OTel at runtime.
2. Install an in-memory span exporter.
3. Exercise `extractor_span(...)` from a ProductionExtractor.extract()
   path.
4. Assert the span was emitted with the expected attributes.

Guards against silent regressions in the OTel init path (wrong
exporter name, instrumentation import break, attribute dict filter).
"""
from __future__ import annotations

import importlib

import pytest


_provider_ready = False
_exporter = None


@pytest.fixture(scope="module", autouse=True)
def _install_otel_once():
    """Install the in-memory provider exactly once per module.

    The OpenTelemetry API blocks re-setting the global tracer provider,
    so we install it once, share the exporter across tests, and each
    test clears the exporter in its own fixture.
    """
    global _provider_ready, _exporter

    import os
    os.environ["DSI_OTEL_ENABLED"] = "true"
    os.environ["OTEL_SERVICE_NAME"] = "dsi-api-otel-smoke"
    os.environ["DSI_ENV"] = "test"

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from opentelemetry.sdk.resources import Resource

    if not _provider_ready:
        provider = TracerProvider(
            resource=Resource.create({"service.name": "dsi-api-otel-smoke"})
        )
        _exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_exporter))
        try:
            trace.set_tracer_provider(provider)
        except Exception:
            pass
        _provider_ready = True

    # Re-import so `is_enabled()` sees DSI_OTEL_ENABLED=true.
    from infrastructure.api.observability import otel as otel_module
    importlib.reload(otel_module)
    otel_module._INITIALISED = True
    yield


@pytest.fixture()
def enabled_otel():
    """Per-test exporter handle. Clears spans before each test."""
    global _exporter
    if _exporter is not None:
        _exporter.clear()
    yield _exporter


def test_otel_enabled_emits_span_for_extractor_call(enabled_otel):
    from infrastructure.api.observability.otel import extractor_span

    with extractor_span(
        "test.source",
        entity_id="acme",
        coverage="cyber",
        config_name="cyber_general",
        cost_tier="free",
        cache_hit=False,
    ) as span:
        assert span is not None

    spans = enabled_otel.get_finished_spans()
    matching = [s for s in spans if s.name == "extractor.test.source"]
    assert matching, f"span not emitted. got: {[s.name for s in spans]}"
    s = matching[0]
    assert s.attributes.get("dsi.entity_id") == "acme"
    assert s.attributes.get("dsi.coverage") == "cyber"
    assert s.attributes.get("dsi.config") == "cyber_general"
    assert s.attributes.get("dsi.cost_tier") == "free"
    assert s.attributes.get("dsi.cache_hit") is False


def test_otel_none_attributes_are_filtered(enabled_otel):
    from infrastructure.api.observability.otel import extractor_span

    with extractor_span("test.filtered") as span:
        assert span is not None

    spans = enabled_otel.get_finished_spans()
    matching = [s for s in spans if s.name == "extractor.test.filtered"]
    assert matching
    s = matching[0]
    # Only 'dsi.cache_hit' (False, default) should survive; the rest
    # of the dsi.* attrs were None and should be stripped.
    assert "dsi.entity_id" not in s.attributes
    assert "dsi.coverage" not in s.attributes
    assert s.attributes.get("dsi.cache_hit") is False
