"""V7 Phase 10 — root-cause clustering + canonicalisation."""
from __future__ import annotations

from datetime import datetime

import pytest

from signal_architecture.signals.routing.dedup_keys import (
    canonical_docket,
    canonical_entity_name,
    canonical_identifier,
)
from signal_architecture.signals.routing.root_cause_cluster import (
    ContributingObservation,
    RootCauseCluster,
    cluster_deterministic,
    maybe_llm_merge,
)


def _obs(*, source, ref, fact_class="sdn_listing", det_key=None, date=None, weight=1.0, payload=None):
    return ContributingObservation(
        source_id=source,
        canonical_entity_ref=ref,
        event_date=date,
        fact_class=fact_class,
        deterministic_key=det_key,
        payload=payload or {"source": source, "ref": ref},
        weight=weight,
    )


# ---------------------------------------------------------------------------
# canonicalisation
# ---------------------------------------------------------------------------

class TestCanonicalEntityName:
    def test_strips_legal_suffix(self):
        assert canonical_entity_name("Acme Corporation Ltd") == "acme corporation"
        assert canonical_entity_name("Acme Inc.") == "acme"
        assert canonical_entity_name("Foo Bar GmbH") == "foo bar"

    def test_strips_punctuation_and_collapses_whitespace(self):
        assert canonical_entity_name("  Acme,  Inc.  ") == "acme"
        assert canonical_entity_name("A.B.C. Holdings PLC") == "a b c holdings"

    def test_case_insensitive(self):
        assert canonical_entity_name("ACME LTD") == canonical_entity_name("acme ltd")

    def test_only_strips_one_suffix(self):
        # "co ltd" — only the trailing 'ltd' is stripped, 'co' stays.
        assert canonical_entity_name("Trading Co Ltd") == "trading co"

    def test_empty(self):
        assert canonical_entity_name("") == ""
        assert canonical_entity_name("   ") == ""


class TestCanonicalDocket:
    def test_strips_label_prefix(self):
        assert canonical_docket("Case No. 1:21-cv-04567") == canonical_docket("1:21-cv-04567")

    def test_removes_whitespace(self):
        assert canonical_docket("21 cv 04567") == "21cv04567"

    def test_empty(self):
        assert canonical_docket("") == ""


class TestCanonicalIdentifier:
    def test_normalises_lei(self):
        assert canonical_identifier("549300-ABC.123") == "549300abc123"

    def test_case_insensitive(self):
        assert canonical_identifier("ABC123") == canonical_identifier("abc123")


# ---------------------------------------------------------------------------
# cluster_deterministic
# ---------------------------------------------------------------------------

class TestClusterDeterministic:
    def test_same_authoritative_id_collapses(self):
        # Three sources, same OFAC list ID -> ONE cluster.
        obs = [
            _obs(source="ofac", ref="acme", det_key="OFAC-12345"),
            _obs(source="opensanctions", ref="acme corp", det_key="OFAC-12345"),
            _obs(source="news", ref="acme corporation", det_key="OFAC-12345"),
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 1
        assert clusters[0].contributor_count == 3
        assert clusters[0].source_ids == ["ofac", "opensanctions", "news"]

    def test_distinct_authoritative_ids_stay_separate(self):
        # Same name, two genuinely different listings -> TWO clusters.
        obs = [
            _obs(source="ofac", ref="acme", det_key="OFAC-12345"),
            _obs(source="ofac", ref="acme", det_key="OFAC-99999"),
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 2

    def test_no_id_clusters_by_name_and_date_bucket(self):
        # No authoritative ID — same name + same date bucket -> one cluster.
        d = datetime(2026, 3, 15)
        obs = [
            _obs(source="a", ref="acme", date=d),
            _obs(source="b", ref="acme", date=datetime(2026, 3, 20)),  # within 30d bucket
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 1
        assert clusters[0].contributor_count == 2

    def test_no_id_different_names_stay_separate(self):
        d = datetime(2026, 3, 15)
        obs = [
            _obs(source="a", ref="acme", date=d),
            _obs(source="b", ref="globex", date=d),
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 2

    def test_order_independent(self):
        obs_a = [
            _obs(source="ofac", ref="acme", det_key="X1"),
            _obs(source="news", ref="acme", det_key="X1"),
            _obs(source="ofac", ref="globex", det_key="X2"),
        ]
        obs_b = list(reversed(obs_a))
        ca = cluster_deterministic(obs_a)
        cb = cluster_deterministic(obs_b)
        assert [c.cluster_id for c in ca] == [c.cluster_id for c in cb]
        assert [c.contributor_count for c in ca] == [c.contributor_count for c in cb]

    def test_symptoms_preserved(self):
        obs = [
            _obs(source="ofac", ref="acme", det_key="X1", payload={"raw": "ofac record"}),
            _obs(source="news", ref="acme", det_key="X1", payload={"raw": "news record"}),
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 1
        symptoms = clusters[0].symptoms
        assert {"raw": "ofac record"} in symptoms
        assert {"raw": "news record"} in symptoms

    def test_empty_input(self):
        assert cluster_deterministic([]) == []

    def test_cluster_id_stable_across_runs(self):
        obs = [_obs(source="ofac", ref="acme", det_key="X1")]
        c1 = cluster_deterministic(obs)
        c2 = cluster_deterministic(obs)
        assert c1[0].cluster_id == c2[0].cluster_id

    def test_news_event_uses_narrower_bucket(self):
        # news_event uses a 7-day bucket; 15 days apart -> separate clusters.
        obs = [
            _obs(source="a", ref="acme", fact_class="news_event", date=datetime(2026, 3, 1)),
            _obs(source="b", ref="acme", fact_class="news_event", date=datetime(2026, 3, 16)),
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 2


# ---------------------------------------------------------------------------
# maybe_llm_merge
# ---------------------------------------------------------------------------

class TestMaybeLLMMerge:
    def test_noop_when_no_llm(self):
        obs = [
            _obs(source="a", ref="acme holdings"),
            _obs(source="b", ref="acme holdngs"),  # near-dup, no det key
        ]
        clusters = cluster_deterministic(obs)
        # Without an LLM, the near-dup clusters stay separate.
        merged = maybe_llm_merge(clusters, llm_callable=None)
        assert len(merged) == len(clusters)

    def test_llm_merges_near_duplicates(self):
        obs = [
            _obs(source="a", ref="acme holdings"),
            _obs(source="b", ref="acme holdngs"),  # 1 char off -> >0.85 similar
        ]
        clusters = cluster_deterministic(obs)
        assert len(clusters) == 2  # deterministic pass keeps them apart

        merged = maybe_llm_merge(
            clusters, llm_callable=lambda a, b: True, similarity_floor=0.85,
        )
        assert len(merged) == 1
        assert merged[0].deterministic is False  # LLM was involved
        assert merged[0].contributor_count == 2

    def test_llm_declines_keeps_separate(self):
        obs = [
            _obs(source="a", ref="acme holdings"),
            _obs(source="b", ref="acme holdngs"),
        ]
        clusters = cluster_deterministic(obs)
        merged = maybe_llm_merge(
            clusters, llm_callable=lambda a, b: False, similarity_floor=0.85,
        )
        assert len(merged) == 2

    def test_below_similarity_floor_not_shown_to_llm(self):
        calls = []
        obs = [
            _obs(source="a", ref="acme holdings"),
            _obs(source="b", ref="globex industries"),  # totally different
        ]
        clusters = cluster_deterministic(obs)

        def _llm(a, b):
            calls.append((a, b))
            return True

        merged = maybe_llm_merge(clusters, llm_callable=_llm, similarity_floor=0.85)
        # The LLM was never consulted because similarity < floor.
        assert calls == []
        assert len(merged) == 2

    def test_different_fact_class_never_merged(self):
        obs = [
            _obs(source="a", ref="acme holdings", fact_class="sdn_listing"),
            _obs(source="b", ref="acme holdings", fact_class="corporate_record"),
        ]
        clusters = cluster_deterministic(obs)
        merged = maybe_llm_merge(
            clusters, llm_callable=lambda a, b: True, similarity_floor=0.85,
        )
        # Same ref, but different fact_class -> LLM never sees the pair.
        assert len(merged) == 2
