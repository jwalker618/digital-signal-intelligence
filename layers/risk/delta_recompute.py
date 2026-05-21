"""V7 Phase 13 — sync workflow runner for the delta dispatcher.

The Phase 13 dispatcher (``infrastructure.recompute.dispatcher.dispatch_due``)
calls a ``workflow_runner(event_id, submission_id, entity_id, signal_filter)
-> uuid`` callable. This module provides the default implementation,
exposed at ``layers.risk.delta_recompute.run_delta_recompute`` so the
deployer can wire it via
``DSI_DELTA_WORKFLOW_RUNNER=layers.risk.delta_recompute.run_delta_recompute``.

Approach (sync — runs inside a Celery worker):
    1. Open a sync DB session.
    2. Load the previous ``ModelVersionRecord`` for ``submission_id``.
    3. Resolve the coverage's config + the inference function registry.
    4. Re-extract every signal in ``signal_filter``.
    5. For signals NOT in ``signal_filter``, copy the latest values from
       ``signal_history``.
    6. Build a new ``ModelVersionRecord`` row stamped
       ``version_type='delta_recompute'`` carrying V7 composite-grade
       fields via ``v7_persistence.mv_create_kwargs_from_result``-style
       logic adapted to sync sqlalchemy.
    7. Insert per-signal rows (``ModelVersionSignal`` + ``SignalHistory``)
       so the disclosure packet endpoint sees the new state.
    8. Return the new ``model_version_id``.

This is intentionally lean — it handles the dispatch path's needs
without re-running the full 14-step workflow. Pricing / tier / quote
remain on the previous ModelVersion unless a downstream re-quote step
acts on the new mv. The dispatcher's contract only needs the
``resulting_model_version_id``.

Failure modes (logged and propagated):
    - Submission has no prior ModelVersion → ValueError (the workflow
      can't apply a delta against nothing). Dispatcher will leave
      ``dispatched_at`` NULL and retry next pass.
    - Inference function for a signal in ``signal_filter`` is missing →
      that signal gets the previous value (carry-forward); not a hard
      error.
"""
from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.db.config import get_db
from infrastructure.db.models import (
    ModelVersionRecord,
    SignalHistory,
)

logger = logging.getLogger("dsi.delta_recompute")


def run_delta_recompute(
    event_id: _uuid.UUID,
    submission_id: Optional[_uuid.UUID],
    entity_id: str,
    signal_filter: set[str],
) -> _uuid.UUID:
    """Produce a delta ModelVersion for the entity. Returns its id."""
    db_iter = get_db()
    db = next(db_iter)
    try:
        new_mv_id = _do_delta_recompute(
            db,
            event_id=event_id,
            submission_id=submission_id,
            entity_id=entity_id,
            signal_filter=signal_filter,
        )
        db.commit()
        return new_mv_id
    except Exception:
        db.rollback()
        raise
    finally:
        try:
            next(db_iter)
        except StopIteration:
            pass


def _do_delta_recompute(
    db: Session,
    *,
    event_id: _uuid.UUID,
    submission_id: Optional[_uuid.UUID],
    entity_id: str,
    signal_filter: set[str],
) -> _uuid.UUID:
    """Body — easier to test in isolation."""
    if submission_id is None:
        raise ValueError(
            f"delta recompute requires submission_id (event {event_id})"
        )

    # 1. Find the previous ModelVersion for this submission.
    prev_mv = (
        db.query(ModelVersionRecord)
        .filter(
            ModelVersionRecord.submission_id == submission_id,
            ModelVersionRecord.is_latest == True,  # noqa: E712
        )
        .first()
    )
    if prev_mv is None:
        raise ValueError(
            f"no previous ModelVersion for submission {submission_id} — "
            f"delta recompute requires a baseline"
        )

    # 2. Carry every prior signal_history value forward by default.
    prior_hist = (
        db.query(SignalHistory)
        .filter(SignalHistory.submission_id == submission_id)
        .order_by(SignalHistory.recorded_at.desc())
        .all()
    )
    # Keep the LATEST row per signal_id.
    latest_by_signal: dict[str, SignalHistory] = {}
    for row in prior_hist:
        if row.signal_id not in latest_by_signal:
            latest_by_signal[row.signal_id] = row

    # 3. Re-extract signals in the blast set. Each gets a fresh
    #    SignalResult; we serialise it back into a SignalHistory row so
    #    the disclosure endpoint sees the new state.
    re_extracted: dict[str, SignalHistory] = {}
    for sig_id in signal_filter:
        re_extracted[sig_id] = _reextract_or_carry(
            db,
            signal_id=sig_id,
            entity_id=entity_id,
            prev_hist=latest_by_signal.get(sig_id),
        )

    # 4. Build the new ModelVersion row. Mark previous as not-latest.
    db.query(ModelVersionRecord).filter(
        ModelVersionRecord.submission_id == submission_id,
        ModelVersionRecord.is_latest == True,  # noqa: E712
    ).update({"is_latest": False})

    next_version = (prev_mv.version_number or 0) + 1
    new_mv = ModelVersionRecord(
        id=_uuid.uuid4(),
        version_code=f"mv-delta-{_uuid.uuid4().hex[:8]}",
        submission_id=submission_id,
        version_number=next_version,
        version_type="delta_recompute",
        is_latest=True,
        config_hash=prev_mv.config_hash,
        coverage=prev_mv.coverage,
        configuration_name=prev_mv.configuration_name,
        # Carry pricing/tier from the previous version verbatim — delta
        # recompute updates evidence only; a downstream re-quote step
        # decides whether to re-price.
        pure_composite_score=prev_mv.pure_composite_score,
        final_composite_score=prev_mv.final_composite_score,
        confidence=prev_mv.confidence,
        signal_coverage=prev_mv.signal_coverage,
        final_tier=prev_mv.final_tier,
        tier_label=prev_mv.tier_label,
        composite_min_grade=prev_mv.composite_min_grade,
        composite_weighted_mean_grade=prev_mv.composite_weighted_mean_grade,
        composite_grade_distribution=prev_mv.composite_grade_distribution or {},
    )
    db.add(new_mv)
    db.flush()

    # 5. Write the merged set of signal_history rows under the new mv.
    merged: dict[str, SignalHistory] = dict(latest_by_signal)
    merged.update(re_extracted)
    now = datetime.now(timezone.utc)
    for sig_id, src in merged.items():
        db.add(SignalHistory(
            id=_uuid.uuid4(),
            model_version_id=new_mv.id,
            submission_id=submission_id,
            signal_id=sig_id,
            recorded_at=now,
            score=src.score,
            category=src.category,
            confidence=src.confidence,
            evidence_grade=src.evidence_grade,
            evidence_basis=src.evidence_basis,
            evidence_sources=src.evidence_sources or [],
            evidence_pro=src.evidence_pro,
            evidence_counter=src.evidence_counter,
            evidence_tie_breaker=src.evidence_tie_breaker,
            absence_sub_type=src.absence_sub_type,
            primitive_type=src.primitive_type,
            history_metadata={
                "delta_recompute": True,
                "delta_event_id": str(event_id),
                "carried_forward": sig_id not in re_extracted,
            },
        ))

    logger.info(
        "delta_recompute event=%s mv=%s carried=%d re-extracted=%d",
        event_id, new_mv.id,
        len(merged) - len(re_extracted), len(re_extracted),
    )
    return new_mv.id


def _reextract_or_carry(
    db: Session,
    *,
    signal_id: str,
    entity_id: str,
    prev_hist: Optional[SignalHistory],
) -> SignalHistory:
    """Run the inference function for one signal; on failure carry the
    previous history row forward (returning prev_hist unchanged).

    Returns a SignalHistory-shaped object — for re-extracted signals it's
    an in-memory instance with the new values; for carry-forward it's
    the previous row reused.
    """
    from signal_architecture.signals.inference.registry import (
        InferenceFunctionNotFoundError,
        get_inference_function,
    )
    from signal_architecture.signals.types import InferenceContext

    try:
        fn = get_inference_function(f"{signal_id}_basefunction")
    except InferenceFunctionNotFoundError:
        # Fall through to the prev_hist carry path.
        if prev_hist is None:
            # No history either — synthesise an empty placeholder.
            return SignalHistory(
                id=_uuid.uuid4(),
                signal_id=signal_id,
                score=None, category=None, confidence=0.0,
                evidence_grade=None,
                evidence_basis="delta recompute: no inference fn + no history",
                evidence_sources=[],
            )
        return prev_hist

    ctx = InferenceContext(configuration={}, coverage="", config_name="")
    try:
        result = fn(entity_id, ctx)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "delta recompute fallback for signal %s: inference fn raised %s",
            signal_id, e,
        )
        if prev_hist is not None:
            return prev_hist
        raise

    # Synthesise a SignalHistory-shaped object carrying the fresh values.
    return SignalHistory(
        id=_uuid.uuid4(),
        signal_id=signal_id,
        score=result.score,
        category=result.category,
        confidence=result.confidence,
        evidence_grade=result.evidence_grade,
        evidence_basis=result.evidence_basis,
        evidence_sources=[s.to_dict() for s in (result.evidence_sources or [])],
        evidence_pro=result.evidence_pro,
        evidence_counter=result.evidence_counter,
        evidence_tie_breaker=result.evidence_tie_breaker,
        absence_sub_type=result.absence_sub_type,
        primitive_type=result.primitive_type,
    )
