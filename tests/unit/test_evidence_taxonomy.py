"""V7 Phase 1 — evidence taxonomy tests.

Distinct from V6's `test_evidence.py`, which covers the evidence-dashboard
snapshot. This file targets `signal_architecture.signals.evidence`.
"""
import pytest
from datetime import datetime, timezone

from signal_architecture.signals.evidence import (
    EVIDENCE_GRADES,
    EvidenceSource,
    bump_evidence,
    evidence_at_or_above,
    evidence_compare,
    evidence_rank,
)


class TestRanking:
    def test_grades_are_ordered(self):
        ranks = [evidence_rank(g) for g in EVIDENCE_GRADES]
        assert ranks == sorted(ranks)
        assert len(set(ranks)) == len(ranks)

    def test_compare(self):
        assert evidence_compare("inferred", "observed") == -1
        assert evidence_compare("structured_attested", "structured_attested") == 0
        assert evidence_compare("behaviourally_validated", "corroborated") == 1

    def test_at_or_above(self):
        assert evidence_at_or_above("structured_attested", "observed") is True
        assert evidence_at_or_above("observed", "structured_attested") is False
        assert evidence_at_or_above("observed", "observed") is True


class TestBump:
    def test_none_promotes_to_anything(self):
        assert bump_evidence(None, "inferred") == "inferred"
        assert bump_evidence(None, "structured_attested") == "structured_attested"

    def test_monotonic(self):
        assert bump_evidence("inferred", "observed") == "observed"
        assert bump_evidence("observed", "inferred") == "observed"  # never demotes
        assert bump_evidence("corroborated", "corroborated") == "corroborated"

    def test_rejects_unknown(self):
        with pytest.raises(ValueError):
            bump_evidence("inferred", "made_up")  # type: ignore[arg-type]

    def test_tolerates_garbage_current(self):
        # Forward-compat: an unknown current value gets overwritten cleanly.
        assert bump_evidence("legacy_value", "observed") == "observed"  # type: ignore[arg-type]


class TestEvidenceSource:
    def test_roundtrip(self):
        s = EvidenceSource(
            source_id="sec_edgar",
            kind="register",
            ref="https://www.sec.gov/cgi-bin/browse-edgar?...",
            fetched_at=datetime.now(timezone.utc),
            response_hash="abc123",
            notes="10-K filing",
        )
        d = s.to_dict()
        assert EvidenceSource.from_dict(d) == s

    def test_minimum_fields_roundtrip(self):
        s = EvidenceSource(
            source_id="x",
            kind="api",
            ref="https://api.example.com/v1/x",
            fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        d = s.to_dict()
        assert d["response_hash"] is None
        assert d["notes"] == ""
        assert EvidenceSource.from_dict(d) == s


class TestSignalResultEvidenceFields:
    """SignalResult should accept and validate the new V7 fields."""

    def test_default_construction_leaves_evidence_unset(self):
        from signal_architecture.signals.types import SignalResult
        r = SignalResult(signal_id="x")
        assert r.evidence_grade is None
        assert r.evidence_basis is None
        assert r.evidence_sources == []
        assert r.evidence_pro is None
        assert r.evidence_counter is None
        assert r.evidence_tie_breaker is None

    def test_evidence_basis_too_long_rejected(self):
        from signal_architecture.signals.types import SignalResult
        with pytest.raises(ValueError):
            SignalResult(signal_id="x", evidence_basis="x" * 501)

    def test_empty_evidence_basis_rejected(self):
        from signal_architecture.signals.types import SignalResult
        with pytest.raises(ValueError):
            SignalResult(signal_id="x", evidence_basis="")

    def test_evidence_basis_at_limit_accepted(self):
        from signal_architecture.signals.types import SignalResult
        r = SignalResult(signal_id="x", evidence_basis="x" * 500)
        assert r.evidence_basis is not None and len(r.evidence_basis) == 500
