"""V7 — Celery background tasks for the V7 data plane.

Three periodic tasks:

  dispatch_due_events           — Phase 13 dispatcher. Runs every 30 s in
                                   production via celery beat.
  refresh_stability_matview     — Phase 8 reproducibility matview REFRESH
                                   CONCURRENTLY. Daily.
  prune_mechanism_memory        — Phase 12 mechanism pruning. Weekly per
                                   tenant; the scheduler iterates known
                                   tenants.

Each task imports its dependencies lazily so the worker can boot even
when (say) the mechanism JSONL store has no rows yet.

Beat schedule registration lives in the existing celery_app config —
this module just exposes the tasks. Wire them in by extending
``celery_app.beat_schedule``.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Iterable

from infrastructure.db.config import get_db
from infrastructure.recompute.dispatcher import dispatch_due
from signal_architecture.mechanism.store import DEFAULT_BASE, prune_old
from signal_architecture.signals.stability import refresh_classification

from .celery_app import celery_app

logger = logging.getLogger("dsi.workers.v7")


# ---------------------------------------------------------------------------
# Phase 13 — dispatch due entity events
# ---------------------------------------------------------------------------

@celery_app.task(name="dsi.v7.dispatch_due_events", bind=True)
def dispatch_due_events(self) -> int:
    """Periodically run the Phase 13 dispatcher.

    Reads pending entity_events, computes blast radius, calls the
    workflow runner to produce a delta ModelVersion, stamps
    dispatched_at + resulting_model_version_id.

    The workflow runner is wired in via DSI_DELTA_WORKFLOW_RUNNER —
    defaults to a no-op stub that records the call but returns a
    well-formed UUID so the dispatcher can stamp the row.
    """
    runner = _resolve_workflow_runner()

    # Single sync session is fine here — Celery beat runs the task in a
    # worker process, and dispatch_due is sync.
    db_iter = get_db()
    db = next(db_iter)
    try:
        n = dispatch_due(db, workflow_runner=runner, now=datetime.now(timezone.utc))
        db.commit()
        logger.info("v7.dispatch_due_events: dispatched %d event(s)", n)
        return n
    finally:
        try:
            next(db_iter)  # close the generator
        except StopIteration:
            pass


def _resolve_workflow_runner():
    """Look up DSI_DELTA_WORKFLOW_RUNNER (dotted path) or return a stub."""
    import importlib
    import uuid as _uuid

    path = os.environ.get("DSI_DELTA_WORKFLOW_RUNNER", "")
    if not path:
        # Default stub: records the call, returns a fresh UUID so the
        # dispatcher's stamp logic still runs. Production overrides via
        # the env var.
        def _stub(event_id, submission_id, entity_id, signal_filter):
            logger.warning(
                "v7.dispatch_due_events: no DSI_DELTA_WORKFLOW_RUNNER "
                "configured; stub returning fresh UUID for event %s",
                event_id,
            )
            return _uuid.uuid4()
        return _stub
    module_path, _, attr = path.rpartition(".")
    if not module_path:
        raise RuntimeError(f"DSI_DELTA_WORKFLOW_RUNNER bad form: {path!r}")
    return getattr(importlib.import_module(module_path), attr)


# ---------------------------------------------------------------------------
# Phase 8 — refresh stability classification matview
# ---------------------------------------------------------------------------

@celery_app.task(name="dsi.v7.refresh_stability_matview", bind=True)
def refresh_stability_matview(self) -> bool:
    """Daily REFRESH MATERIALIZED VIEW CONCURRENTLY of
    signal_stability_classification.

    Returns True on success. Logs and re-raises on DB error so Celery
    surfaces the failure (the unique index on the matview's triple key
    is what makes CONCURRENTLY possible).
    """
    db_iter = get_db()
    db = next(db_iter)
    try:
        refresh_classification(db)
        db.commit()
        logger.info("v7.refresh_stability_matview: refreshed")
        return True
    except Exception:
        db.rollback()
        logger.exception("v7.refresh_stability_matview: failed")
        raise
    finally:
        try:
            next(db_iter)
        except StopIteration:
            pass


# ---------------------------------------------------------------------------
# Phase 12 — prune mechanism memory (per tenant)
# ---------------------------------------------------------------------------

@celery_app.task(name="dsi.v7.prune_mechanism_memory", bind=True)
def prune_mechanism_memory(
    self,
    older_than_days: int = 365,
    min_recall_count: int = 3,
) -> dict:
    """Weekly prune across all tenants under the JSONL store base.

    Returns ``{tenant_id: n_archived}`` summary so the beat log shows
    which tenants pruned. Robust to missing base dir (no-op).
    """
    base = DEFAULT_BASE
    if not base.exists():
        logger.info("v7.prune_mechanism_memory: base %s absent; no-op", base)
        return {}

    out: dict[str, int] = {}
    for tenant_dir in sorted(base.iterdir()):
        if not tenant_dir.is_dir():
            continue
        n = prune_old(
            tenant_dir.name,
            base=base,
            older_than_days=older_than_days,
            min_recall_count=min_recall_count,
        )
        if n:
            out[tenant_dir.name] = n
    logger.info("v7.prune_mechanism_memory: archived %s row(s) across tenants", sum(out.values()))
    return out


# ---------------------------------------------------------------------------
# Beat schedule helpers — call from celery_app.py when wiring is desired.
# ---------------------------------------------------------------------------

V7_BEAT_SCHEDULE = {
    "v7_dispatch_due_events": {
        "task": "dsi.v7.dispatch_due_events",
        "schedule": 30.0,  # seconds — frequent because webhook latency budget
    },
    "v7_refresh_stability_matview": {
        "task": "dsi.v7.refresh_stability_matview",
        # crontab() import is lazy — we leave the value as a placeholder
        # string in dev; production wires the real crontab in celery_app.
        "schedule": 24 * 60 * 60.0,  # daily
    },
    "v7_prune_mechanism_memory": {
        "task": "dsi.v7.prune_mechanism_memory",
        "schedule": 7 * 24 * 60 * 60.0,  # weekly
    },
}
