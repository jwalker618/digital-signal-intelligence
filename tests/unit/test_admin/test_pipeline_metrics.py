"""B-1d: PipelineMetrics helpers (no DB required)."""

from datetime import datetime, timedelta, timezone

from infrastructure.admin.pipeline_metrics import (
    PipelineMetrics,
    PipelineSnapshot,
    _safe_float,
)


class TestPeriodStart:
    def test_1h(self):
        as_of = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        start = PipelineMetrics._period_start(as_of, "1h")
        assert (as_of - start) == timedelta(hours=1)

    def test_24h(self):
        as_of = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        start = PipelineMetrics._period_start(as_of, "24h")
        assert (as_of - start) == timedelta(hours=24)

    def test_7d(self):
        as_of = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        start = PipelineMetrics._period_start(as_of, "7d")
        assert (as_of - start) == timedelta(days=7)

    def test_30d(self):
        as_of = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        start = PipelineMetrics._period_start(as_of, "30d")
        assert (as_of - start) == timedelta(days=30)

    def test_unknown_defaults_to_24h(self):
        as_of = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        start = PipelineMetrics._period_start(as_of, "nonsense")
        assert (as_of - start) == timedelta(hours=24)


class TestSafeFloat:
    def test_none(self):
        assert _safe_float(None) is None

    def test_int(self):
        assert _safe_float(42) == 42.0

    def test_float(self):
        assert _safe_float(1.5) == 1.5

    def test_decimal_like(self):
        from decimal import Decimal
        assert _safe_float(Decimal("3.14")) == 3.14

    def test_invalid_returns_none(self):
        assert _safe_float("not a number") is None


class TestPipelineSnapshot:
    def test_defaults(self):
        snap = PipelineSnapshot(
            captured_at=datetime.now(timezone.utc),
            period="24h",
        )
        assert snap.assessments_total == 0
        assert snap.failure_rate == 0.0
        assert snap.decision_mix == {}
        assert snap.latency_p50_ms is None
