"""V7 Phase 8 — stability store: record_observation, lookup_class, annotate."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.stability import (
    annotate_signals_with_reproducibility,
    lookup_class,
    record_observation,
)
from signal_architecture.signals.types import SignalResult
from infrastructure.db.models import SignalStabilityObservation


def _sig(score=72.0, sources=None):
    return SignalResult(
        signal_id="x", score=score, confidence=1.0,
        evidence_grade="observed", evidence_basis="b",
        evidence_sources=sources or [],
    )


def _src(sid="ofac"):
    return EvidenceSource(
        source_id=sid, kind="register",
        ref=f"https://example.com/{sid}",
        fetched_at=datetime.now(timezone.utc),
    )


class TestRecordObservation:
    def test_builds_observation_row(self):
        db = MagicMock()
        record_observation(
            db, _sig(score=72.0),
            source_id="ofac", entity_id="acme",
            race_sensitive=False, response_hash="resp123",
        )
        assert db.add.call_count == 1
        row = db.add.call_args[0][0]
        assert isinstance(row, SignalStabilityObservation)
        assert row.source_id == "ofac"
        assert row.signal_id == "x"
        assert row.entity_id == "acme"
        assert row.value_score == 72.0
        assert row.race_sensitive is False
        assert row.response_hash == "resp123"
        assert row.value_hash  # set

    def test_race_sensitive_flag_carried(self):
        db = MagicMock()
        record_observation(
            db, _sig(), source_id="bgp", entity_id="acme",
            race_sensitive=True,
        )
        row = db.add.call_args[0][0]
        assert row.race_sensitive is True


class TestLookupClass:
    def test_returns_unknown_when_no_row(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = None
        result = lookup_class(
            db, source_id="ofac", signal_id="x", entity_id="acme",
        )
        assert result == "unknown"

    def test_returns_matview_class(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = ("stable",)
        result = lookup_class(
            db, source_id="ofac", signal_id="x", entity_id="acme",
        )
        assert result == "stable"


class TestAnnotateSignals:
    def test_signal_with_no_sources_gets_unknown(self):
        db = MagicMock()
        sig = _sig(sources=[])
        annotate_signals_with_reproducibility(db, [sig], entity_id="acme")
        assert sig.reproducibility == "unknown"
        # No DB lookup needed
        db.execute.assert_not_called()

    def test_signal_with_sources_gets_matview_class(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = ("flaky",)
        sig = _sig(sources=[_src("ofac")])
        annotate_signals_with_reproducibility(db, [sig], entity_id="acme")
        assert sig.reproducibility == "flaky"

    def test_uses_primary_source(self):
        """Lookup keys on evidence_sources[0]."""
        db = MagicMock()
        db.execute.return_value.first.return_value = ("stable",)
        sig = _sig(sources=[_src("primary"), _src("secondary")])
        annotate_signals_with_reproducibility(db, [sig], entity_id="acme")
        # Inspect the bound params passed to execute()
        _, kwargs = db.execute.call_args
        params = db.execute.call_args[0][1]
        assert params["s"] == "primary"

    def test_annotates_multiple_signals(self):
        db = MagicMock()
        db.execute.return_value.first.return_value = ("stable",)
        sigs = [_sig(sources=[_src()]) for _ in range(3)]
        annotate_signals_with_reproducibility(db, sigs, entity_id="acme")
        for s in sigs:
            assert s.reproducibility == "stable"
