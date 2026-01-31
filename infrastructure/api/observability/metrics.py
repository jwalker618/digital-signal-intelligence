"""
DSI Prometheus Metrics

Instruments the API with Prometheus counters, histograms, and gauges
for production monitoring.
"""

import time
from typing import Optional

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)


class DSIMetrics:
    """Central metrics registry for the DSI platform."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        reg = registry or REGISTRY

        # --- Request metrics ---
        self.request_duration = Histogram(
            "dsi_request_duration_seconds",
            "HTTP request duration in seconds",
            labelnames=["method", "endpoint", "status_code"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=reg,
        )

        self.request_total = Counter(
            "dsi_requests_total",
            "Total HTTP requests",
            labelnames=["method", "endpoint", "status_code"],
            registry=reg,
        )

        self.errors_total = Counter(
            "dsi_errors_total",
            "Total errors by type",
            labelnames=["error_type"],
            registry=reg,
        )

        # --- Business metrics ---
        self.submissions_total = Counter(
            "dsi_submissions_total",
            "Total submissions processed",
            labelnames=["coverage", "status"],
            registry=reg,
        )

        self.quotes_total = Counter(
            "dsi_quotes_total",
            "Total quotes generated",
            labelnames=["coverage", "decision"],
            registry=reg,
        )

        self.referrals_total = Counter(
            "dsi_referrals_total",
            "Total referrals created",
            labelnames=["coverage", "reason"],
            registry=reg,
        )

        # --- Pipeline metrics ---
        self.scoring_duration = Histogram(
            "dsi_scoring_duration_seconds",
            "Scoring pipeline duration in seconds",
            labelnames=["coverage"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=reg,
        )

        self.signal_extraction_duration = Histogram(
            "dsi_signal_extraction_seconds",
            "Signal extraction duration in seconds",
            labelnames=["signal_id", "source"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=reg,
        )

        self.workflow_duration = Histogram(
            "dsi_workflow_duration_seconds",
            "Full workflow duration (submission to decision)",
            labelnames=["coverage"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=reg,
        )

        # --- System metrics ---
        self.active_workflows = Gauge(
            "dsi_active_workflows",
            "Number of currently running workflows",
            registry=reg,
        )

        self.db_connected = Gauge(
            "dsi_database_connected",
            "Whether the database is connected (1=yes, 0=no)",
            registry=reg,
        )

        self.cache_connected = Gauge(
            "dsi_cache_connected",
            "Whether Redis cache is connected (1=yes, 0=no)",
            registry=reg,
        )

        self.info = Info(
            "dsi",
            "DSI platform information",
            registry=reg,
        )

    def observe_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record an HTTP request."""
        # Normalize endpoint to avoid cardinality explosion
        normalized = self._normalize_endpoint(endpoint)
        self.request_duration.labels(
            method=method, endpoint=normalized, status_code=str(status_code)
        ).observe(duration)
        self.request_total.labels(
            method=method, endpoint=normalized, status_code=str(status_code)
        ).inc()

    def observe_submission(self, coverage: str, status: str):
        """Record a submission event."""
        self.submissions_total.labels(coverage=coverage, status=status).inc()

    def observe_quote(self, coverage: str, decision: str):
        """Record a quote generation."""
        self.quotes_total.labels(coverage=coverage, decision=decision).inc()

    def observe_referral(self, coverage: str, reason: str):
        """Record a referral."""
        self.referrals_total.labels(coverage=coverage, reason=reason).inc()

    def observe_scoring(self, coverage: str, duration: float):
        """Record scoring pipeline duration."""
        self.scoring_duration.labels(coverage=coverage).observe(duration)

    def observe_signal_extraction(self, signal_id: str, source: str, duration: float):
        """Record signal extraction duration."""
        self.signal_extraction_duration.labels(
            signal_id=signal_id, source=source
        ).observe(duration)

    def observe_workflow(self, coverage: str, duration: float):
        """Record full workflow duration."""
        self.workflow_duration.labels(coverage=coverage).observe(duration)

    def record_error(self, error_type: str):
        """Record an error."""
        self.errors_total.labels(error_type=error_type).inc()

    def set_info(self, version: str, environment: str):
        """Set platform info."""
        self.info.info({"version": version, "environment": environment})

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """Normalize endpoint paths to avoid high cardinality.

        /api/v1/submissions/abc123 → /api/v1/submissions/{id}
        """
        parts = path.rstrip("/").split("/")
        normalized = []
        for i, part in enumerate(parts):
            # Replace UUIDs and numeric IDs with {id}
            if i > 0 and (
                len(part) > 8
                or (part.isdigit() and i > 2)
                or ("-" in part and len(part) > 20)
            ):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


# Singleton metrics instance
metrics = DSIMetrics()


def get_metrics_response():
    """Generate Prometheus text format response."""
    from fastapi.responses import Response
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
