"""OpenTelemetry bootstrap (V6 Phase 6 / C3).

Installs a singleton TracerProvider + OTLP exporter and attaches
auto-instrumentation to FastAPI, SQLAlchemy, Redis, and outbound HTTP
(requests + httpx). An `extractor_span` helper is exposed for per-extractor
spans — used by the production extractor base once D1/D3 land.

The module is a no-op unless ``DSI_OTEL_ENABLED=true``; production
deployments set it via the ConfigMap, local dev defaults off.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator, Optional

log = logging.getLogger("dsi.otel")

_INITIALISED = False
_NOOP_TRACER = None


def _as_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _endpoint() -> Optional[str]:
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv("DSI_OTEL_ENDPOINT")


def is_enabled() -> bool:
    return _as_bool(os.getenv("DSI_OTEL_ENABLED"), default=False)


def init_otel(app: Any = None, engine: Any = None) -> None:
    """Initialise tracing + instrumentation.

    Safe to call multiple times (idempotent). When disabled, does nothing.
    Missing optional OpenTelemetry packages degrade gracefully with a
    warning log rather than raising.
    """
    global _INITIALISED
    if _INITIALISED or not is_enabled():
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:
        log.warning(
            "opentelemetry-sdk / OTLP exporter not installed; "
            "tracing disabled. Install extras 'otel'."
        )
        return

    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "dsi-api"),
        "service.version": os.getenv("DSI_VERSION", "unknown"),
        "deployment.environment": os.getenv("DSI_ENV", "development"),
    })
    provider = TracerProvider(resource=resource)
    exporter_endpoint = _endpoint()
    exporter_kwargs = {}
    if exporter_endpoint:
        exporter_kwargs["endpoint"] = exporter_endpoint
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs)))
    trace.set_tracer_provider(provider)

    # Best-effort auto-instrumentation — each import is optional.
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except ImportError:
            log.debug("opentelemetry-instrumentation-fastapi not installed; skipping.")

    if engine is not None:
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument(engine=engine)
        except ImportError:
            log.debug("opentelemetry-instrumentation-sqlalchemy not installed; skipping.")

    for inst_module, inst_cls in (
        ("opentelemetry.instrumentation.requests", "RequestsInstrumentor"),
        ("opentelemetry.instrumentation.httpx",     "HTTPXClientInstrumentor"),
        ("opentelemetry.instrumentation.redis",     "RedisInstrumentor"),
    ):
        try:
            module = __import__(inst_module, fromlist=[inst_cls])
            getattr(module, inst_cls)().instrument()
        except ImportError:
            log.debug("%s not installed; skipping.", inst_module)

    _INITIALISED = True
    log.info(
        "OpenTelemetry initialised: endpoint=%s service=%s env=%s",
        exporter_endpoint or "(default)",
        os.getenv("OTEL_SERVICE_NAME", "dsi-api"),
        os.getenv("DSI_ENV", "development"),
    )


def _tracer():
    try:
        from opentelemetry import trace
        return trace.get_tracer("dsi")
    except ImportError:
        return None


@contextmanager
def extractor_span(
    source_name: str,
    *,
    entity_id: Optional[str] = None,
    coverage: Optional[str] = None,
    config_name: Optional[str] = None,
    cost_tier: Optional[str] = None,
    cache_hit: bool = False,
    attributes: Optional[dict] = None,
) -> Iterator[Any]:
    """Emit a span named ``extractor.<source_name>`` with DSI attributes.

    Always yields — if OTel isn't initialised, yields ``None`` so callers
    don't need to branch. Attributes unknown to the backend are stripped.
    """
    tracer = _tracer()
    if tracer is None:
        yield None
        return
    attrs = {
        "dsi.entity_id": entity_id,
        "dsi.coverage": coverage,
        "dsi.config": config_name,
        "dsi.cost_tier": cost_tier,
        "dsi.cache_hit": cache_hit,
    }
    if attributes:
        attrs.update(attributes)
    # Drop None values — OTel SDK rejects them.
    attrs = {k: v for k, v in attrs.items() if v is not None}
    with tracer.start_as_current_span(f"extractor.{source_name}", attributes=attrs) as span:
        yield span
