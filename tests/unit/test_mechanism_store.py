"""V7 Phase 12 — JSONL store: append (idempotent), update_recall, prune."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from signal_architecture.mechanism import (
    Mechanism,
    append,
    existing_signatures,
    load_all,
    prune_old,
    update_recall,
)


def _m(*, summary="entity pattern abc", primitive="governance", recall=0, last=0.0, first=None):
    return Mechanism(
        id=f"mech-{summary[:6]}",
        summary=summary,
        primitive_type=primitive,
        sector_tags=["do", "fi"],
        tags=["board_overlap"],
        keywords=["board", "overlap"],
        what_made_it_high_grade="reasons",
        source_cluster_id="C1",
        source_signal_id="director_litigation",
        source_cycle_id="mv-1",
        first_seen=first if first is not None else time.time(),
        last_recalled_at=last,
        recall_count=recall,
    )


class TestAppendIdempotent:
    def test_appends_once(self, tmp_path):
        m = _m()
        assert append("t1", m, base=tmp_path) is True
        assert append("t1", m, base=tmp_path) is False  # signature collision
        assert len(load_all("t1", base=tmp_path)) == 1

    def test_signature_keys_on_summary_plus_primitive(self, tmp_path):
        # Same summary, different primitive -> distinct rows.
        m1 = _m(primitive="governance")
        m2 = _m(primitive="financial")
        m2.id = "mech-other"  # avoid id collision (id is incidental)
        assert append("t1", m1, base=tmp_path) is True
        assert append("t1", m2, base=tmp_path) is True
        assert len(load_all("t1", base=tmp_path)) == 2

    def test_canonical_signature_case_insensitive(self):
        a = _m(summary="entity pattern abc")
        b = _m(summary="ENTITY pattern abc")
        assert a.canonical_signature == b.canonical_signature

    def test_existing_signatures_set_correct(self, tmp_path):
        m = _m()
        append("t1", m, base=tmp_path)
        sigs = existing_signatures("t1", base=tmp_path)
        assert m.canonical_signature in sigs


class TestTenantIsolation:
    def test_cross_tenant_invisible(self, tmp_path):
        m_a = _m(summary="alpha pattern")
        m_b = _m(summary="beta pattern")
        append("tenant_a", m_a, base=tmp_path)
        append("tenant_b", m_b, base=tmp_path)
        a = load_all("tenant_a", base=tmp_path)
        b = load_all("tenant_b", base=tmp_path)
        assert [x.summary for x in a] == ["alpha pattern"]
        assert [x.summary for x in b] == ["beta pattern"]

    def test_path_uses_tenant_subdir(self, tmp_path):
        m = _m()
        append("tenant_xyz", m, base=tmp_path)
        assert (tmp_path / "tenant_xyz" / "mechanisms.jsonl").exists()
        # Other tenants get their own subdir, not co-mingled.
        assert not (tmp_path / "mechanisms.jsonl").exists()


class TestUpdateRecall:
    def test_increments_count_and_stamps_time(self, tmp_path):
        m = _m()
        append("t1", m, base=tmp_path)
        now = 1_700_000_000.0
        assert update_recall("t1", m.id, base=tmp_path, now=now) is True
        rows = load_all("t1", base=tmp_path)
        assert rows[0].recall_count == 1
        assert rows[0].last_recalled_at == now

    def test_returns_false_when_not_found(self, tmp_path):
        m = _m()
        append("t1", m, base=tmp_path)
        assert update_recall("t1", "missing-id", base=tmp_path) is False

    def test_returns_false_on_empty_store(self, tmp_path):
        assert update_recall("nobody", "missing-id", base=tmp_path) is False


class TestPruneOld:
    def test_archives_stale_low_recall(self, tmp_path):
        now = 1_700_000_000.0
        old_first = now - 400 * 86400
        # Stale, low recall -> archived.
        a = _m(summary="stale a", first=old_first, last=0.0, recall=1)
        # Recently recalled -> kept.
        b = _m(summary="fresh b", first=old_first, last=now - 10, recall=1)
        # High recall, ancient -> kept (recall_count >= min).
        c = _m(summary="popular c", first=old_first, last=0.0, recall=5)
        for m in (a, b, c):
            append("t1", m, base=tmp_path)
        archived = prune_old(
            "t1", base=tmp_path,
            older_than_days=365, min_recall_count=3, now=now,
        )
        assert archived == 1
        remaining = {m.summary for m in load_all("t1", base=tmp_path)}
        assert remaining == {"fresh b", "popular c"}
        # Archive file contains the pruned row.
        archive_path = tmp_path / "t1" / "mechanisms_archive.jsonl"
        assert archive_path.exists()
        archived_rows = [json.loads(l) for l in archive_path.read_text().splitlines() if l]
        assert any(r["summary"] == "stale a" for r in archived_rows)

    def test_no_op_when_nothing_stale(self, tmp_path):
        now = time.time()
        m = _m(first=now, last=now, recall=0)
        append("t1", m, base=tmp_path)
        assert prune_old("t1", base=tmp_path, now=now) == 0
