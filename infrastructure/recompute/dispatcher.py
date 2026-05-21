"""V7 Phase 13 — event dispatcher: receive -> compute blast -> dispatch.

`receive_event()` inserts a row into `entity_events` and computes the
blast radius eagerly so it's visible to the activity view (Phase 14).
Dedup-by-key is built in so a webhook retry doesn't double-process.

`dispatch_due()` iterates undispatched events, enforces a per-entity
rate window, calls the caller-supplied workflow runner with the blast
filter, and stamps `dispatched_at` + `resulting_model_version_id`.

The workflow runner is supplied as a callable rather than imported to
keep this module DB-free for testing and orchestration-loop-free at
import time.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from infrastructure.db.compliance_audit_store import (
    EVENT_DELTA_RECOMPUTE_COMPLETED,
    EVENT_DELTA_RECOMPUTE_STARTED,
    EVENT_ENTITY_EVENT_RECEIVED,
    log_event,
)
from infrastructure.db.models import EntityEvent

from .blast_radius import compute_blast_radius

logger = logging.getLogger("dsi.recompute.dispatcher")

# Per-entity rate window. Subsequent events within this window are NOT
# re-dispatched until the previous dispatch is older than this. Prevents
# webhook storms from blowing up the workflow queue.
_RATE_WINDOW = timedelta(hours=1)


def receive_event(
    db: Session,
    *,
    event_type: str,
    source_feed: str,
    entity_id: str,
    payload: dict,
    dedup_key: Optional[str] = None,
    submission_id: Optional[uuid.UUID] = None,
    hinted_signal_id: Optional[str] = None,
) -> EntityEvent:
    """Insert an entity_events row (or return the existing one on dedup hit).

    Computes blast_radius eagerly so the row is self-describing.
    Writes EVENT_ENTITY_EVENT_RECEIVED to compliance_audit_logs.
    Caller commits.
    """
    if dedup_key:
        existing = (
            db.query(EntityEvent)
            .filter_by(dedup_key=dedup_key)
            .one_or_none()
        )
        if existing is not None:
            return existing

    blast = sorted(
        compute_blast_radius(
            event_type=event_type,
            hinted_signal_id=hinted_signal_id,
        )
    )
    row = EntityEvent(
        event_type=event_type,
        source_feed=source_feed,
        entity_id=entity_id,
        submission_id=submission_id,
        dedup_key=dedup_key,
        payload=payload,
        blast_radius=blast,
    )
    db.add(row)
    db.flush()
    log_event(
        db,
        event_type=EVENT_ENTITY_EVENT_RECEIVED,
        submission_id=submission_id,
        payload={
            "entity_id": entity_id,
            "event_type": event_type,
            "source_feed": source_feed,
            "blast_size": len(blast),
        },
    )
    return row


# Workflow runner: (event_id, submission_id, entity_id, signal_filter)
#   -> resulting_model_version_id
WorkflowRunner = Callable[
    [uuid.UUID, Optional[uuid.UUID], str, set[str]],
    uuid.UUID,
]


def _recent_dispatch_exists(
    db: Session,
    *,
    entity_id: str,
    now: datetime,
) -> bool:
    cutoff = now - _RATE_WINDOW
    q = db.query(EntityEvent).filter(
        EntityEvent.entity_id == entity_id,
        EntityEvent.dispatched_at.isnot(None),
        EntityEvent.dispatched_at >= cutoff,
    )
    return q.first() is not None


def dispatch_due(
    db: Session,
    *,
    workflow_runner: WorkflowRunner,
    now: Optional[datetime] = None,
) -> int:
    """Process undispatched events. Returns the number dispatched.

    Enforces the per-entity rate window: if an event for the same entity
    was dispatched within the past hour, the new event waits (it stays
    `dispatched_at IS NULL`). The next dispatch_due() call after the
    window opens picks it up.
    """
    now = now or datetime.now(timezone.utc)
    pending = (
        db.query(EntityEvent)
        .filter(EntityEvent.dispatched_at.is_(None))
        .order_by(EntityEvent.received_at.asc())
        .all()
    )
    dispatched = 0
    for ev in pending:
        if _recent_dispatch_exists(db, entity_id=ev.entity_id, now=now):
            continue
        blast = set(ev.blast_radius or [])
        log_event(
            db,
            event_type=EVENT_DELTA_RECOMPUTE_STARTED,
            submission_id=ev.submission_id,
            payload={
                "event_id": str(ev.id),
                "entity_id": ev.entity_id,
                "signals": sorted(blast),
            },
        )
        try:
            new_mv_id = workflow_runner(ev.id, ev.submission_id, ev.entity_id, blast)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "delta recompute failed for event %s: %s", ev.id, e,
            )
            # Leave dispatched_at NULL so the next pass retries — but log
            # the failure for visibility.
            log_event(
                db,
                event_type=EVENT_DELTA_RECOMPUTE_COMPLETED,
                submission_id=ev.submission_id,
                payload={
                    "event_id": str(ev.id),
                    "error": str(e),
                },
            )
            continue
        ev.dispatched_at = datetime.now(timezone.utc)
        ev.resulting_model_version_id = new_mv_id
        dispatched += 1
        log_event(
            db,
            event_type=EVENT_DELTA_RECOMPUTE_COMPLETED,
            submission_id=ev.submission_id,
            model_version_id=new_mv_id,
            payload={
                "event_id": str(ev.id),
                "signals": sorted(blast),
            },
        )
    return dispatched
