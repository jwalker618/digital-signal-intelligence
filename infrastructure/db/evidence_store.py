"""V7 Phase 5 — read/write helpers for evidence columns + signal_history.

Two operations:

  - `persist_signal_evidence(db, mvs_row, sig)`: update the
    `ModelVersionSignal` row in place with V7 fields AND append an
    immutable `SignalHistory` row.

  - `latest_history_for_signal(db, submission_id, signal_id)`: read the
    most recent history row for a (submission, signal_id) pair. Useful
    for the workbench / disclosure-packet path in Phase 14.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import ModelVersionSignal, SignalHistory
from signal_architecture.signals.types import SignalResult


def persist_signal_evidence(
    db: Session,
    *,
    mvs_row: ModelVersionSignal,
    sig: SignalResult,
    submission_id: uuid.UUID,
) -> None:
    """Update mvs_row in place + append a SignalHistory row.

    Caller is expected to ``db.add`` the history row implicitly via SQLAlchemy
    Session.add inside this function. Caller commits at cycle end.
    """
    sources_dicts = [s.to_dict() for s in (sig.evidence_sources or [])]

    # In-place update of the model_version_signals row.
    mvs_row.evidence_grade = sig.evidence_grade
    mvs_row.evidence_basis = sig.evidence_basis
    mvs_row.evidence_sources = sources_dicts
    mvs_row.evidence_pro = sig.evidence_pro
    mvs_row.evidence_counter = sig.evidence_counter
    mvs_row.evidence_tie_breaker = sig.evidence_tie_breaker
    mvs_row.absence_sub_type = sig.absence_sub_type

    # Append immutable history row. (uq_signal_history_per_mv_signal on
    # (model_version_id, signal_id, recorded_at) prevents accidental
    # double-write within the same instant.)
    db.add(SignalHistory(
        model_version_id=mvs_row.model_version_id,
        submission_id=submission_id,
        signal_id=sig.signal_id,
        recorded_at=datetime.now(timezone.utc),
        score=sig.score,
        category=sig.category,
        confidence=sig.confidence,
        evidence_grade=sig.evidence_grade,
        evidence_basis=sig.evidence_basis,
        evidence_sources=sources_dicts,
        evidence_pro=sig.evidence_pro,
        evidence_counter=sig.evidence_counter,
        evidence_tie_breaker=sig.evidence_tie_breaker,
        absence_sub_type=sig.absence_sub_type,
        history_metadata=sig.metadata or {},
    ))


def latest_history_for_signal(
    db: Session,
    *,
    submission_id: uuid.UUID,
    signal_id: str,
) -> Optional[SignalHistory]:
    """Most recent SignalHistory row for the (submission, signal) pair."""
    return (
        db.query(SignalHistory)
        .filter_by(submission_id=submission_id, signal_id=signal_id)
        .order_by(SignalHistory.recorded_at.desc())
        .first()
    )
