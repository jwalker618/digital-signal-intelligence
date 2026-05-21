"""V7 Phase 5 — commitment_store tests.

DB access is mocked: we intercept ``db.add(...)`` to inspect the
SignalCommitment rows the store would have persisted. Determinism and
verify-roundtrip are unit-tested at the canonical-bytes layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from infrastructure.db.commitment_store import (
    _payload_for_scope,
    commit_composite,
    commit_signal,
    sha3_224,
    verify,
)
from infrastructure.db.models import SignalCommitment
from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.types import SignalResult


def _sig():
    return SignalResult(
        signal_id="sanctions_check",
        score=95.0,
        confidence=0.85,
        evidence_grade="structured_attested",
        evidence_basis="OFAC + UK OFSI multi-source clear",
        evidence_sources=[EvidenceSource(
            source_id="ofac",
            kind="register",
            ref="https://sanctionssearch.ofac.treas.gov",
            fetched_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        )],
        evidence_pro="No matches across two independent registers",
        evidence_counter="Source coverage is US/UK only",
        evidence_tie_breaker="OFAC SDN list refreshed within 24 hours",
        absence_sub_type="absence_authoritative_empty",
    )


class TestDeterminism:
    def test_same_payload_same_digest(self):
        a = sha3_224({"a": 1, "b": 2})
        b = sha3_224({"b": 2, "a": 1})  # key reordered
        assert a == b

    def test_different_payload_different_digest(self):
        a = sha3_224({"a": 1})
        b = sha3_224({"a": 2})
        assert a != b

    def test_datetime_serialised_deterministically(self):
        d = datetime(2026, 1, 1, tzinfo=timezone.utc)
        a = sha3_224({"t": d})
        b = sha3_224({"t": d})
        assert a == b


class TestPayloadForScope:
    def test_full_payload_includes_sources(self):
        payload, keys = _payload_for_scope(_sig(), "full_payload")
        assert "evidence_sources" in payload
        assert payload["evidence_grade"] == "structured_attested"
        assert payload["evidence_pro"]
        assert payload["absence_sub_type"] == "absence_authoritative_empty"

    def test_value_and_grade_minimal(self):
        payload, keys = _payload_for_scope(_sig(), "value_and_grade")
        assert set(payload.keys()) == {"signal_id", "score", "category", "evidence_grade"}

    def test_pro_counter_excludes_value(self):
        payload, keys = _payload_for_scope(_sig(), "pro_counter")
        assert "score" not in payload
        assert payload["evidence_pro"]
        assert payload["evidence_counter"]

    def test_unknown_scope_raises(self):
        with pytest.raises(ValueError):
            _payload_for_scope(_sig(), "badscope")  # type: ignore[arg-type]


class TestCommitSignal:
    def test_persists_row_with_expected_fields(self):
        db = MagicMock()
        mv_id = uuid.uuid4()
        digest = commit_signal(db, model_version_id=mv_id, sig=_sig(), scope="value_and_grade")
        # Inspect the row passed to db.add
        assert db.add.call_count == 1
        row = db.add.call_args[0][0]
        assert isinstance(row, SignalCommitment)
        assert row.model_version_id == mv_id
        assert row.signal_id == "sanctions_check"
        assert row.scope == "value_and_grade"
        assert row.algorithm == "sha3_224"
        assert row.digest == digest
        assert len(digest) == 56  # SHA3-224 hex length

    def test_full_payload_digest_differs_from_value_and_grade(self):
        db = MagicMock()
        mv_id = uuid.uuid4()
        a = commit_signal(db, model_version_id=mv_id, sig=_sig(), scope="full_payload")
        b = commit_signal(db, model_version_id=mv_id, sig=_sig(), scope="value_and_grade")
        assert a != b


class TestCommitComposite:
    def test_composite_commitment_no_signal_id(self):
        db = MagicMock()
        mv_id = uuid.uuid4()
        digest = commit_composite(
            db, model_version_id=mv_id,
            composite_min_grade="observed",
            composite_weighted_mean_grade=2.4,
            composite_grade_distribution={"observed": 0.6, "structured_attested": 0.4},
            referral_reasons=["share of weight below 0.5"],
        )
        row = db.add.call_args[0][0]
        assert row.signal_id is None
        assert row.scope == "composite"
        assert row.digest == digest

    def test_referral_reasons_order_independent(self):
        """sorted(referral_reasons) baked into the canonical payload."""
        db = MagicMock()
        mv_id = uuid.uuid4()
        a = commit_composite(
            db, model_version_id=mv_id,
            composite_min_grade="observed",
            composite_weighted_mean_grade=2.4,
            composite_grade_distribution={"observed": 1.0},
            referral_reasons=["a", "b"],
        )
        b = commit_composite(
            db, model_version_id=mv_id,
            composite_min_grade="observed",
            composite_weighted_mean_grade=2.4,
            composite_grade_distribution={"observed": 1.0},
            referral_reasons=["b", "a"],
        )
        assert a == b


class TestVerify:
    def test_match_returns_true(self):
        # Build a fake row matching what commit_signal would write
        sig = _sig()
        from infrastructure.db.commitment_store import _payload_for_scope
        payload, keys = _payload_for_scope(sig, "value_and_grade")
        expected_digest = sha3_224(payload)

        row = SignalCommitment(
            digest=expected_digest, scope="value_and_grade", algorithm="sha3_224",
        )
        db = MagicMock()
        db.query.return_value.filter_by.return_value.one_or_none.return_value = row

        ok = verify(
            db, model_version_id=uuid.uuid4(),
            signal_id="x", scope="value_and_grade",
            candidate_payload=payload,
        )
        assert ok is True

    def test_mismatch_returns_false(self):
        row = SignalCommitment(digest="0" * 56, scope="value_and_grade")
        db = MagicMock()
        db.query.return_value.filter_by.return_value.one_or_none.return_value = row
        ok = verify(
            db, model_version_id=uuid.uuid4(),
            signal_id="x", scope="value_and_grade",
            candidate_payload={"tampered": True},
        )
        assert ok is False

    def test_missing_row_returns_false(self):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.one_or_none.return_value = None
        ok = verify(
            db, model_version_id=uuid.uuid4(),
            signal_id="x", scope="full_payload",
            candidate_payload={},
        )
        assert ok is False
