"""V7 Phase 13 — dispatcher: receive_event + dispatch_due (mock DB)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from infrastructure.db.models import EntityEvent
from infrastructure.recompute.dispatcher import (
    _RATE_WINDOW,
    dispatch_due,
    receive_event,
)


def _db_with_no_dedup_hit():
    """Mock Session: dedup lookup returns None."""
    db = MagicMock()
    db.query.return_value.filter_by.return_value.one_or_none.return_value = None
    return db


def _db_with_dedup_hit(existing):
    db = MagicMock()
    db.query.return_value.filter_by.return_value.one_or_none.return_value = existing
    return db


class TestReceiveEvent:
    def test_inserts_with_blast_radius_eager(self):
        db = _db_with_no_dedup_hit()
        ev = receive_event(
            db,
            event_type="sanctions_update",
            source_feed="ofac",
            entity_id="ent1",
            payload={"id": "X"},
            dedup_key="ofac:X",
        )
        assert isinstance(ev, EntityEvent)
        assert ev.event_type == "sanctions_update"
        assert ev.entity_id == "ent1"
        assert ev.dedup_key == "ofac:X"
        # blast_radius computed eagerly; must contain known sanctions signals.
        assert "sanctions_screening_result" in ev.blast_radius

    def test_dedup_returns_existing_row(self):
        existing = EntityEvent(
            id=uuid.uuid4(), event_type="sanctions_update",
            entity_id="ent1", source_feed="ofac",
            dedup_key="ofac:X", payload={},
        )
        db = _db_with_dedup_hit(existing)
        ev = receive_event(
            db,
            event_type="sanctions_update",
            source_feed="ofac",
            entity_id="ent1",
            payload={},
            dedup_key="ofac:X",
        )
        # No new row added.
        assert ev is existing
        db.add.assert_not_called()

    def test_no_dedup_key_always_inserts(self):
        db = _db_with_no_dedup_hit()
        receive_event(
            db,
            event_type="manual_recompute",
            source_feed="manual",
            entity_id="ent1",
            payload={},
        )
        # db.add called for the EntityEvent row + the audit log row.
        assert db.add.call_count >= 1


class TestDispatchDue:
    def _pending_event(self, *, eid="A", entity="ent1", blast=None):
        ev = EntityEvent(
            id=uuid.uuid4(),
            event_type="sanctions_update",
            entity_id=entity,
            source_feed="ofac",
            payload={},
            blast_radius=blast or ["sanctions_screening_result"],
        )
        # Make received_at sortable.
        ev.received_at = datetime.now(timezone.utc) - timedelta(seconds=int(eid, 36) if isinstance(eid, str) and eid.isalnum() else 1)
        return ev

    def _db_with_pending(self, events, *, recent_dispatch=False):
        """Mock DB that:
          - returns `events` for the pending query
          - returns recent_dispatch presence for the rate-window check
        """
        db = MagicMock()

        def query_side_effect(model):
            qres = MagicMock()
            qres.filter.return_value = qres
            qres.order_by.return_value = qres
            qres.all.return_value = events
            # Rate-window check uses .first(); we control it via flag.
            qres.first.return_value = MagicMock() if recent_dispatch else None
            return qres

        db.query.side_effect = query_side_effect
        return db

    def test_dispatches_when_no_recent(self):
        ev = self._pending_event()
        db = self._db_with_pending([ev], recent_dispatch=False)
        new_mv_id = uuid.uuid4()
        runner = MagicMock(return_value=new_mv_id)
        n = dispatch_due(db, workflow_runner=runner)
        assert n == 1
        runner.assert_called_once()
        # Event got stamped.
        assert ev.dispatched_at is not None
        assert ev.resulting_model_version_id == new_mv_id

    def test_skips_when_within_rate_window(self):
        ev = self._pending_event()
        db = self._db_with_pending([ev], recent_dispatch=True)
        runner = MagicMock()
        n = dispatch_due(db, workflow_runner=runner)
        assert n == 0
        runner.assert_not_called()
        assert ev.dispatched_at is None  # left for next pass

    def test_runner_exception_keeps_event_pending(self):
        ev = self._pending_event()
        db = self._db_with_pending([ev], recent_dispatch=False)

        def boom(*args, **kwargs):
            raise RuntimeError("workflow failed")

        n = dispatch_due(db, workflow_runner=boom)
        assert n == 0
        assert ev.dispatched_at is None  # NOT stamped — retried next pass

    def test_runner_called_with_blast_set(self):
        ev = self._pending_event(blast=["a", "b", "c"])
        db = self._db_with_pending([ev], recent_dispatch=False)
        runner = MagicMock(return_value=uuid.uuid4())
        dispatch_due(db, workflow_runner=runner)
        args, kwargs = runner.call_args
        # workflow_runner signature: (event_id, submission_id, entity_id, signal_filter)
        assert args[0] == ev.id
        assert args[3] == {"a", "b", "c"}


class TestRateWindowConstant:
    def test_rate_window_is_one_hour(self):
        assert _RATE_WINDOW == timedelta(hours=1)
