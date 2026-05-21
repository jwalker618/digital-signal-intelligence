"""V7 — Celery worker tasks for dispatch / matview / prune.

Tasks are tested by exercising their underlying function bodies via
``.run(...)`` (not ``.delay()``). Celery's `bind=True` arg becomes the
first positional argument, so we pass a sentinel for `self`.

DB sessions are mocked because the env has no live postgres.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.workers.v7_tasks import (
    V7_BEAT_SCHEDULE,
    _resolve_workflow_runner,
    dispatch_due_events,
    prune_mechanism_memory,
    refresh_stability_matview,
)


def _stub_session():
    """A Session-shaped mock that also supports the generator-close pattern
    `next(db_iter)` -> StopIteration."""
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


def _stub_get_db(db):
    """Yield a single session, then close — matches FastAPI Depends pattern."""
    def _gen():
        yield db
    return _gen()


# ---------------------------------------------------------------------------
# _resolve_workflow_runner
# ---------------------------------------------------------------------------

class TestResolveRunner:
    def test_default_stub_returns_uuid(self):
        runner = _resolve_workflow_runner()
        out = runner(uuid.UUID(int=1), None, "entity", {"x"})
        assert isinstance(out, uuid.UUID)

    def test_dotted_path_resolves(self):
        # Plant a fake module-attr to resolve to.
        import types
        mod = types.ModuleType("dsi_test_runner_mod")
        mod.my_runner = lambda *a, **kw: uuid.UUID(int=42)
        import sys
        sys.modules["dsi_test_runner_mod"] = mod
        try:
            with patch.dict(os.environ, {"DSI_DELTA_WORKFLOW_RUNNER": "dsi_test_runner_mod.my_runner"}):
                runner = _resolve_workflow_runner()
                assert runner() == uuid.UUID(int=42)
        finally:
            sys.modules.pop("dsi_test_runner_mod", None)

    def test_bad_form_raises(self):
        with patch.dict(os.environ, {"DSI_DELTA_WORKFLOW_RUNNER": "no_dot"}):
            with pytest.raises(RuntimeError):
                _resolve_workflow_runner()


# ---------------------------------------------------------------------------
# dispatch_due_events
# ---------------------------------------------------------------------------

class TestDispatchDueEvents:
    def test_calls_dispatcher_and_commits(self):
        db = _stub_session()
        with patch("infrastructure.workers.v7_tasks.get_db", return_value=_stub_get_db(db)), \
             patch("infrastructure.workers.v7_tasks.dispatch_due", return_value=3) as dd:
            n = dispatch_due_events.run()
        assert n == 3
        dd.assert_called_once()
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# refresh_stability_matview
# ---------------------------------------------------------------------------

class TestRefreshMatview:
    def test_calls_refresh_and_commits(self):
        db = _stub_session()
        with patch("infrastructure.workers.v7_tasks.get_db", return_value=_stub_get_db(db)), \
             patch("infrastructure.workers.v7_tasks.refresh_classification") as rc:
            ok = refresh_stability_matview.run()
        assert ok is True
        rc.assert_called_once_with(db)
        db.commit.assert_called_once()

    def test_rollback_on_failure(self):
        db = _stub_session()
        with patch("infrastructure.workers.v7_tasks.get_db", return_value=_stub_get_db(db)), \
             patch("infrastructure.workers.v7_tasks.refresh_classification",
                   side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                refresh_stability_matview.run()
        db.rollback.assert_called_once()
        db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# prune_mechanism_memory
# ---------------------------------------------------------------------------

class TestPruneMechanismMemory:
    def test_no_op_when_base_absent(self, tmp_path):
        with patch("infrastructure.workers.v7_tasks.DEFAULT_BASE", tmp_path / "absent"):
            out = prune_mechanism_memory.run()
            assert out == {}

    def test_prunes_each_tenant(self, tmp_path):
        # Build a base with two tenants, each carrying a stale row.
        from signal_architecture.mechanism import Mechanism, append

        old = 1_700_000_000.0 - 400 * 86400  # comfortably older than 365d cutoff
        for tenant in ("ta", "tb"):
            m = Mechanism(
                id=f"mech-{tenant}", summary=f"pattern {tenant}",
                primitive_type="governance",
                sector_tags=["do"], tags=[], keywords=[],
                what_made_it_high_grade="x",
                source_cluster_id="C", source_signal_id="s",
                source_cycle_id="mv",
                first_seen=old, last_recalled_at=0.0, recall_count=0,
            )
            append(tenant, m, base=tmp_path)

        # Patch both the v7_tasks-local reference (for base = DEFAULT_BASE)
        # AND the store's DEFAULT_BASE (for the prune_old() lookups
        # internal to the task).
        with patch("infrastructure.workers.v7_tasks.DEFAULT_BASE", tmp_path), \
             patch("signal_architecture.mechanism.store.DEFAULT_BASE", tmp_path):
            out = prune_mechanism_memory.run(older_than_days=365, min_recall_count=3)
        assert set(out.keys()) == {"ta", "tb"}
        assert all(v == 1 for v in out.values())


# ---------------------------------------------------------------------------
# Beat schedule shape
# ---------------------------------------------------------------------------

class TestBeatSchedule:
    def test_three_tasks_registered(self):
        assert set(V7_BEAT_SCHEDULE.keys()) == {
            "v7_dispatch_due_events",
            "v7_refresh_stability_matview",
            "v7_prune_mechanism_memory",
        }

    def test_intervals_are_sensible(self):
        s = V7_BEAT_SCHEDULE
        # Dispatch runs frequently (webhook latency budget).
        assert s["v7_dispatch_due_events"]["schedule"] <= 60.0
        # Matview daily-ish.
        assert s["v7_refresh_stability_matview"]["schedule"] >= 23 * 60 * 60
        # Prune weekly-ish.
        assert s["v7_prune_mechanism_memory"]["schedule"] >= 7 * 24 * 60 * 60

    def test_task_names_match_registered_tasks(self):
        for entry in V7_BEAT_SCHEDULE.values():
            assert entry["task"].startswith("dsi.v7.")
