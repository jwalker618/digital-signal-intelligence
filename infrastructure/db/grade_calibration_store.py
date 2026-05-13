"""V7 Phase 7 — grade-calibration data layer.

Four operations:

    persist_samples(db, targets, mv_id, submission_id)
        Inserts new GradeCalibrationSample rows. Idempotent on the
        (model_version_id, signal_id) unique constraint — rows already
        present skipped silently.

    record_human_verdict(db, *, sample_id, human_grade, decided_by, note="")
        Writes a GradeCalibrationDecision + flips the sample to
        state='decided'. Raises LookupError on missing sample, RuntimeError
        on already-decided.

    expire_old(db, *, now=None)
        Flips pending samples past expires_at to state='expired'.

    stats(db, *, coverage=None, window_days=30)
        Aggregates the match flags over a rolling window or lifetime.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import (
    GradeCalibrationDecision,
    GradeCalibrationSample,
)
from signal_architecture.signals.evidence import evidence_rank
from signal_architecture.validation.sampler import SamplingTarget, expiry_for


def persist_samples(
    db: Session,
    targets: Iterable[SamplingTarget],
    *,
    mv_id: uuid.UUID,
    submission_id: uuid.UUID,
    now: Optional[datetime] = None,
) -> int:
    """Append samples idempotently. Returns the number actually inserted."""
    inserted = 0
    exp = expiry_for(now)
    for t in targets:
        c = t.candidate
        existing = (
            db.query(GradeCalibrationSample)
            .filter_by(model_version_id=mv_id, signal_id=c.signal_id)
            .one_or_none()
        )
        if existing is not None:
            continue
        db.add(GradeCalibrationSample(
            model_version_id=mv_id,
            submission_id=submission_id,
            coverage=c.coverage,
            signal_id=c.signal_id,
            signal_weight=c.signal_weight,
            extractor_grade=c.extractor_grade,
            validator_grade=c.validator_grade,
            sampling_reason=t.reason,
            expires_at=exp,
        ))
        inserted += 1
    return inserted


def record_human_verdict(
    db: Session,
    *,
    sample_id: uuid.UUID,
    human_grade: str,
    decided_by: uuid.UUID,
    note: str = "",
) -> GradeCalibrationDecision:
    """Persist the underwriter's verdict + precompute match flags."""
    sample = db.query(GradeCalibrationSample).get(sample_id)
    if sample is None:
        raise LookupError(f"calibration sample {sample_id} not found")
    if sample.state != "pending":
        raise RuntimeError(
            f"calibration sample {sample_id} already in state {sample.state!r}"
        )

    exact_e = sample.extractor_grade == human_grade
    exact_v = (
        sample.validator_grade == human_grade
        if sample.validator_grade is not None
        else None
    )
    try:
        within_one_e = (
            abs(evidence_rank(sample.extractor_grade) - evidence_rank(human_grade)) <= 1
        )
    except KeyError:
        # Defensive: malformed grade strings -> never within_one.
        within_one_e = False

    decision = GradeCalibrationDecision(
        sample_id=sample.id,
        human_grade=human_grade,
        note=note,
        decided_by=decided_by,
        exact_match_extractor=exact_e,
        exact_match_validator=exact_v,
        within_one_extractor=within_one_e,
    )
    db.add(decision)
    sample.state = "decided"
    return decision


def expire_old(
    db: Session,
    *,
    now: Optional[datetime] = None,
) -> int:
    """Flip pending samples past expires_at to state='expired'."""
    now = now or datetime.now(timezone.utc)
    q = db.query(GradeCalibrationSample).filter(
        GradeCalibrationSample.state == "pending",
        GradeCalibrationSample.expires_at < now,
    )
    n = q.count()
    q.update({"state": "expired"})
    return n


@dataclass(frozen=True)
class CalibrationStats:
    """Aggregate match-rate summary for one (coverage?, window?) slice."""
    window_days: Optional[int]
    decided: int
    exact_match_extractor_rate: float
    exact_match_validator_rate: Optional[float]
    within_one_extractor_rate: float

    @property
    def drift_alert_threshold(self) -> float:
        """Below this rate, the 30-day window is considered drifted."""
        return 0.75


def stats(
    db: Session,
    *,
    coverage: Optional[str] = None,
    window_days: Optional[int] = 30,
) -> CalibrationStats:
    """Compute rolling-window or lifetime calibration stats."""
    q = db.query(GradeCalibrationDecision)
    if window_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        q = q.filter(GradeCalibrationDecision.decided_at >= cutoff)
    if coverage is not None:
        q = q.join(GradeCalibrationSample).filter(
            GradeCalibrationSample.coverage == coverage,
        )
    rows = q.all()
    if not rows:
        return CalibrationStats(
            window_days=window_days,
            decided=0,
            exact_match_extractor_rate=0.0,
            exact_match_validator_rate=None,
            within_one_extractor_rate=0.0,
        )
    ex = sum(1 for r in rows if r.exact_match_extractor)
    v_rows = [r for r in rows if r.exact_match_validator is not None]
    v_ex = sum(1 for r in v_rows if r.exact_match_validator)
    w1 = sum(1 for r in rows if r.within_one_extractor)
    return CalibrationStats(
        window_days=window_days,
        decided=len(rows),
        exact_match_extractor_rate=ex / len(rows),
        exact_match_validator_rate=(v_ex / len(v_rows)) if v_rows else None,
        within_one_extractor_rate=w1 / len(rows),
    )


def is_drifted(s: CalibrationStats) -> bool:
    """30-day exact_match_extractor_rate below the documented floor."""
    return (
        s.window_days is not None
        and s.window_days <= 30
        and s.decided > 0
        and s.exact_match_extractor_rate < s.drift_alert_threshold
    )
