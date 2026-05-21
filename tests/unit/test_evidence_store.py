"""V7 Phase 5 — evidence_store tests (mock session)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from infrastructure.db.evidence_store import persist_signal_evidence
from infrastructure.db.models import ModelVersionSignal, SignalHistory
from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.types import SignalResult


def _sig():
    return SignalResult(
        signal_id="x",
        score=72.0,
        confidence=0.9,
        evidence_grade="corroborated",
        evidence_basis="Multi-source agreement",
        evidence_sources=[EvidenceSource(
            source_id="opensanctions", kind="register",
            ref="https://api.opensanctions.org",
            fetched_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        )],
    )


class TestPersistSignalEvidence:
    def test_updates_mvs_row_in_place(self):
        mv_id = uuid.uuid4()
        mvs = ModelVersionSignal(model_version_id=mv_id)
        db = MagicMock()
        persist_signal_evidence(db, mvs_row=mvs, sig=_sig(), submission_id=uuid.uuid4())
        assert mvs.evidence_grade == "corroborated"
        assert mvs.evidence_basis == "Multi-source agreement"
        assert len(mvs.evidence_sources) == 1
        assert mvs.evidence_sources[0]["source_id"] == "opensanctions"

    def test_appends_signal_history_row(self):
        mv_id = uuid.uuid4()
        sub_id = uuid.uuid4()
        mvs = ModelVersionSignal(model_version_id=mv_id)
        db = MagicMock()
        persist_signal_evidence(db, mvs_row=mvs, sig=_sig(), submission_id=sub_id)
        assert db.add.call_count == 1
        history = db.add.call_args[0][0]
        assert isinstance(history, SignalHistory)
        assert history.signal_id == "x"
        assert history.submission_id == sub_id
        assert history.evidence_grade == "corroborated"
        assert history.score == 72.0
        assert len(history.evidence_sources) == 1

    def test_handles_signal_with_no_sources(self):
        mv_id = uuid.uuid4()
        mvs = ModelVersionSignal(model_version_id=mv_id)
        sig = SignalResult(
            signal_id="y", score=50.0, confidence=0.5,
            evidence_grade="inferred", evidence_basis="stub",
        )
        db = MagicMock()
        persist_signal_evidence(db, mvs_row=mvs, sig=sig, submission_id=uuid.uuid4())
        assert mvs.evidence_sources == []
        history = db.add.call_args[0][0]
        assert history.evidence_sources == []

    def test_propagates_absence_sub_type(self):
        mv_id = uuid.uuid4()
        mvs = ModelVersionSignal(model_version_id=mv_id)
        sig = SignalResult(
            signal_id="z", score=95.0, confidence=0.9,
            evidence_grade="structured_attested",
            evidence_basis="OFAC clean screen",
            absence_sub_type="absence_authoritative_empty",
        )
        db = MagicMock()
        persist_signal_evidence(db, mvs_row=mvs, sig=sig, submission_id=uuid.uuid4())
        assert mvs.absence_sub_type == "absence_authoritative_empty"
        history = db.add.call_args[0][0]
        assert history.absence_sub_type == "absence_authoritative_empty"
