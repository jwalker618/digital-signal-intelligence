"""V7 Phase 8 — reproducibility classification.

Reproducibility is a third, orthogonal axis: distinct from confidence
("we got a value") and grade ("what kind of evidence"). It answers
"would the source agree with itself on a re-pull?".

Public API:
    canonical_value_hash(sig)           — stable hash of the asserted value
    record_observation(db, sig, ...)    — append one observation row
    lookup_class(db, ...)               — read the matview-derived class
    refresh_classification(db)          — REFRESH the matview
    classify_ratio(...)                 — pure: agreement ratio -> class
    annotate_signals_with_reproducibility(db, signals, entity_id)

The matview `signal_stability_classification` (alembic 026) does the
heavy aggregation in SQL; `classify_ratio` mirrors that CASE expression
in Python so the logic is unit-testable without a database.
"""
from __future__ import annotations

import hashlib
import json
from typing import Iterable, Literal, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from signal_architecture.signals.types import SignalResult

ReproClass = Literal["stable", "flaky", "unstable", "unknown"]

# Agreement thresholds (distinct_values / n). These mirror the SQL CASE
# in alembic 026's materialised view.
_STABLE_RATIO_DEFAULT = 0.10
_STABLE_RATIO_RACE_SENSITIVE = 0.30
_FLAKY_RATIO = 0.50
_MIN_OBSERVATIONS = 3


def canonical_value_hash(sig: SignalResult) -> str:
    """Stable hash of the value the signal asserts.

    Score is quantised to 1 decimal so negligible numeric drift between
    pulls hashes identically. Category is exact. An empty signal hashes
    to a fixed sentinel.
    """
    if sig.score is not None:
        payload = {"score": round(sig.score, 1)}
    elif sig.category is not None:
        payload = {"category": sig.category}
    else:
        payload = {"empty": True}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def classify_ratio(
    *,
    n: int,
    distinct_values: int,
    race_sensitive: bool,
) -> ReproClass:
    """Pure classifier — mirrors the alembic-026 matview CASE expression.

    n               total observations in the 90-day window
    distinct_values count of distinct value_hash values
    race_sensitive  relaxes the `stable` threshold to 0.30
    """
    if n < _MIN_OBSERVATIONS:
        return "unknown"
    ratio = distinct_values / n
    stable_cut = (
        _STABLE_RATIO_RACE_SENSITIVE if race_sensitive else _STABLE_RATIO_DEFAULT
    )
    if ratio <= stable_cut:
        return "stable"
    if ratio <= _FLAKY_RATIO:
        return "flaky"
    return "unstable"


def record_observation(
    db: Session,
    sig: SignalResult,
    *,
    source_id: str,
    entity_id: str,
    race_sensitive: bool,
    response_hash: Optional[str] = None,
) -> None:
    """Append one immutable observation row. Caller commits."""
    from infrastructure.db.models import SignalStabilityObservation

    db.add(SignalStabilityObservation(
        source_id=source_id,
        signal_id=sig.signal_id,
        entity_id=entity_id,
        value_score=sig.score,
        value_category=sig.category,
        value_hash=canonical_value_hash(sig),
        response_hash=response_hash,
        race_sensitive=race_sensitive,
    ))


def lookup_class(
    db: Session,
    *,
    source_id: str,
    signal_id: str,
    entity_id: str,
) -> ReproClass:
    """Read the matview-derived class for one triple. 'unknown' if absent."""
    row = db.execute(
        text(
            "SELECT class FROM signal_stability_classification "
            "WHERE source_id = :s AND signal_id = :sig AND entity_id = :e"
        ),
        {"s": source_id, "sig": signal_id, "e": entity_id},
    ).first()
    if row is None:
        return "unknown"
    return row[0]


def refresh_classification(db: Session) -> None:
    """REFRESH the reproducibility matview. Run daily by the scheduler."""
    db.execute(
        text("REFRESH MATERIALIZED VIEW CONCURRENTLY signal_stability_classification")
    )


def annotate_signals_with_reproducibility(
    db: Session,
    signals: Iterable[SignalResult],
    *,
    entity_id: str,
) -> None:
    """Set `sig.reproducibility` in place for each signal with sources.

    Called by the workflow after scoring + before commit so the frontend
    sees the class on first render. Signals with no sources -> 'unknown'.
    """
    for sig in signals:
        if not sig.evidence_sources:
            sig.reproducibility = "unknown"
            continue
        primary = sig.evidence_sources[0]
        sig.reproducibility = lookup_class(
            db,
            source_id=primary.source_id,
            signal_id=sig.signal_id,
            entity_id=entity_id,
        )
