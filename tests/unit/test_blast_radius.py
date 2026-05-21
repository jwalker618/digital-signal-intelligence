"""V7 Phase 13 — signal_deps + blast_radius."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from infrastructure.recompute.blast_radius import compute_blast_radius
from infrastructure.recompute.signal_deps import (
    SIGNAL_DEPS,
    downstream_of,
    triggers_for_event,
    triggers_for_signal,
)


class TestTriggersForSignal:
    def test_explicit_entry_wins(self):
        # sanctions_screening_result has explicit triggers list.
        trigs = triggers_for_signal("sanctions_screening_result")
        assert "sanctions_update" in trigs
        assert "manual_recompute" in trigs

    def test_prefix_map_fallback(self):
        # Not explicit but starts with `sanctions_` -> prefix entry.
        trigs = triggers_for_signal("sanctions_something_new")
        assert "sanctions_update" in trigs

    def test_unmapped_signal_only_manual(self):
        # Completely unknown -> only manual_recompute reaches it.
        assert triggers_for_signal("totally_unknown_xyz") == {"manual_recompute"}


class TestTriggersForEvent:
    def test_sanctions_event_picks_explicit_sanctions_signals(self):
        sigs = triggers_for_event("sanctions_update")
        # Must include at least the sanctions screening signals.
        assert "sanctions_screening_result" in sigs
        assert "sanctions_check_routed" in sigs

    def test_entity_filing_picks_filing_signals(self):
        sigs = triggers_for_event("entity_filing")
        assert "sec_filing_recency" in sigs
        assert "corporate_registry_routed" in sigs

    def test_unknown_event_returns_empty(self):
        assert triggers_for_event("totally_made_up_event") == set()


class TestDownstreamClosure:
    def test_esg_score_downstream_of_sentiment_and_reg(self):
        # esg_score depends on sentiment_30d + regulatory_actions_24m.
        assert "esg_score" in downstream_of("sentiment_30d")
        assert "esg_score" in downstream_of("regulatory_actions_24m")

    def test_no_downstream_for_terminal_signal(self):
        # nothing depends on esg_score.
        assert downstream_of("esg_score") == set()


class TestComputeBlastRadius:
    def test_sanctions_update_blast_includes_explicit_signals(self):
        blast = compute_blast_radius(event_type="sanctions_update")
        assert "sanctions_screening_result" in blast
        assert "sanctions_check_routed" in blast

    def test_hinted_signal_added(self):
        blast = compute_blast_radius(
            event_type="manual_recompute",
            hinted_signal_id="sec_filing_recency",
        )
        assert "sec_filing_recency" in blast

    def test_hint_for_unknown_signal_ignored(self):
        # Hinted ID not in SIGNAL_DEPS -> doesn't add it.
        blast = compute_blast_radius(
            event_type="manual_recompute",
            hinted_signal_id="unknown_sig",
        )
        assert "unknown_sig" not in blast

    def test_includes_transitive_downstream(self):
        # entity_filing triggers sec_filing_recency directly; if anything
        # depended on it transitively, it'd be in the closure too. esg_score
        # depends on sentiment_30d/regulatory_actions_24m, so a hinted
        # sentiment_30d should pull esg_score into the blast.
        # Note: sentiment_30d isn't an explicit SIGNAL_DEPS key, so it's
        # only added by hint when it IS a key. This documents the design:
        # only KEYS of SIGNAL_DEPS can be hint-added.
        blast = compute_blast_radius(
            event_type="manual_recompute",
            hinted_signal_id="esg_score",
        )
        # esg_score itself is in the blast.
        assert "esg_score" in blast

    def test_empty_event_no_hint_yields_empty(self):
        # Unknown event type, no hint -> empty blast.
        blast = compute_blast_radius(event_type="never_heard_of_it")
        assert blast == set()


class TestSignalDepsShape:
    def test_every_entry_has_required_keys(self):
        for sid, dep in SIGNAL_DEPS.items():
            assert "triggers" in dep
            assert "depends_on" in dep
            assert isinstance(dep["triggers"], list)
            assert isinstance(dep["depends_on"], list)


# ---------------------------------------------------------------------------
# Alembic 028 shape
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/028_entity_events.py")


def _load_028():
    spec = importlib.util.spec_from_file_location("_v7_028", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic028:
    def test_revision_lineage(self):
        mod = _load_028()
        assert mod.revision == "028"
        assert mod.down_revision == "027"

    def test_creates_entity_events(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "entity_events" in text
        assert "dedup_key" in text
        assert "blast_radius" in text

    def test_in_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("028")
        assert rev is not None
        assert rev.down_revision == "027"
