"""B-1c: ExtractorTracker helpers (no DB required)."""

from datetime import datetime, timezone

from infrastructure.admin.extractor_tracker import (
    LATENCY_EWMA_ALPHA,
    ExtractorHealthRecord,
    ExtractorTracker,
)


class TestComputeFreshness:
    def test_no_ttl_returns_none(self):
        assert ExtractorTracker._compute_freshness(None, datetime.now(timezone.utc), True) is None

    def test_successful_with_ttl_returns_one(self):
        assert ExtractorTracker._compute_freshness(3600, datetime.now(timezone.utc), True) == 1.0

    def test_error_with_ttl_returns_zero(self):
        assert ExtractorTracker._compute_freshness(3600, datetime.now(timezone.utc), False) == 0.0


class TestExtractorHealthRecord:
    def test_success_rate_mixed(self):
        r = ExtractorHealthRecord(
            extractor_id="x", coverage=None, signal_type=None,
            success_count_24h=7, error_count_24h=3,
            avg_latency_ms=150.0,
            last_success_at=None, last_error_at=None, last_error_message=None,
            data_freshness_score=None,
        )
        assert r.success_rate == 0.7

    def test_success_rate_no_data(self):
        r = ExtractorHealthRecord(
            extractor_id="x", coverage=None, signal_type=None,
            success_count_24h=0, error_count_24h=0,
            avg_latency_ms=None,
            last_success_at=None, last_error_at=None, last_error_message=None,
            data_freshness_score=None,
        )
        assert r.success_rate is None

    def test_all_success(self):
        r = ExtractorHealthRecord(
            extractor_id="x", coverage=None, signal_type=None,
            success_count_24h=100, error_count_24h=0,
            avg_latency_ms=None,
            last_success_at=None, last_error_at=None, last_error_message=None,
            data_freshness_score=None,
        )
        assert r.success_rate == 1.0


class TestEwmaConstant:
    def test_alpha_in_range(self):
        assert 0.0 < LATENCY_EWMA_ALPHA < 1.0
