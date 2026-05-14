"""V7 Phase 10 — aggregator-level root-cause clustering.

Tests SanctionsAggregator.cluster_observations and
CorporateAggregator.cluster_observations directly: feed in raw
match/record lists, assert the clustering collapses same-event
observations and preserves the symptom trail.
"""
from __future__ import annotations

from datetime import date

import pytest

from signal_architecture.signals.routing.corporate_aggregator import CorporateAggregator
from signal_architecture.signals.routing.sanctions_aggregator import SanctionsAggregator
from signal_architecture.signals.routing.schemas import (
    CorporateRecord,
    SanctionsMatch,
    SanctionsMatchType,
    SanctionsProgram,
)


# ---------------------------------------------------------------------------
# Sanctions
# ---------------------------------------------------------------------------

def _sanctions_match(*, name, source, source_id=None, score=95.0, desig=None):
    return SanctionsMatch(
        matched_name=name,
        match_type=SanctionsMatchType.EXACT,
        match_score=score,
        source=source,
        source_list=f"{source} list",
        source_id=source_id,
        program=SanctionsProgram.OFAC_SDN,
        designation_date=desig,
    )


class TestSanctionsClustering:
    def test_same_listing_three_sources_collapses_to_one(self):
        agg = SanctionsAggregator()
        matches = [
            _sanctions_match(name="Acme Corp", source="ofac", source_id="SDN-12345", score=98.0),
            _sanctions_match(name="Acme Corporation", source="opensanctions", source_id="SDN-12345", score=90.0),
            _sanctions_match(name="ACME CORP LTD", source="interpol_red_notices", source_id="SDN-12345", score=85.0),
        ]
        reduced, summaries = agg.cluster_observations(matches, "Acme Corp")
        assert len(reduced) == 1
        # Representative is the highest-scoring contributor (ofac, 98.0).
        assert reduced[0].source == "ofac"
        # Cluster metadata + symptoms on the representative's raw_data.
        rd = reduced[0].raw_data
        assert rd["cluster_contributor_count"] == 3
        assert len(rd["symptoms"]) == 3
        assert set(rd["cluster_source_ids"]) == {"ofac", "opensanctions", "interpol_red_notices"}
        # One cluster summary.
        assert len(summaries) == 1
        assert summaries[0]["contributor_count"] == 3

    def test_distinct_listings_stay_separate(self):
        agg = SanctionsAggregator()
        matches = [
            _sanctions_match(name="Acme Corp", source="ofac", source_id="SDN-11111"),
            _sanctions_match(name="Acme Corp", source="ofac", source_id="SDN-22222"),
        ]
        reduced, summaries = agg.cluster_observations(matches, "Acme Corp")
        assert len(reduced) == 2
        assert len(summaries) == 2

    def test_empty_matches_noop(self):
        agg = SanctionsAggregator()
        reduced, summaries = agg.cluster_observations([], "Acme Corp")
        assert reduced == []
        assert summaries == []

    def test_no_authoritative_id_clusters_by_name(self):
        agg = SanctionsAggregator()
        # No source_id — clusters by canonical name + date bucket.
        matches = [
            _sanctions_match(name="Acme Corp", source="a", desig=date(2026, 3, 1)),
            _sanctions_match(name="Acme Corporation Ltd", source="b", desig=date(2026, 3, 10)),
        ]
        reduced, summaries = agg.cluster_observations(matches, "Acme Corp")
        # Both canonicalise to "acme corporation"/"acme corp"...
        # canonical_entity_name strips "Ltd" and "Corp" is NOT a suffix here,
        # so "Acme Corp" -> "acme corp" and "Acme Corporation Ltd" -> "acme corporation".
        # Different canonical refs -> 2 clusters. This documents the
        # conservative-canonicalisation invariant (no fuzzy matching).
        assert len(reduced) == 2


# ---------------------------------------------------------------------------
# Corporate
# ---------------------------------------------------------------------------

def _corp_record(*, name, source, lei=None, reg_no=None, jurisdiction="GB", status="active"):
    return CorporateRecord(
        name=name,
        jurisdiction=jurisdiction,
        registration_number=reg_no,
        lei=lei,
        source=source,
        status=status,
    )


class TestCorporateClustering:
    def test_same_lei_collapses(self):
        agg = CorporateAggregator()
        records = [
            _corp_record(name="Acme Ltd", source="companies_house", lei="ABC123", reg_no="GB12345"),
            _corp_record(name="Acme Limited", source="opencorporates", lei="ABC123"),
            _corp_record(name="ACME LTD", source="gleif_lei", lei="ABC123"),
        ]
        reduced, summaries = agg.cluster_observations(records, "Acme Ltd")
        assert len(reduced) == 1
        # Representative = most-populated record (companies_house has reg_no).
        assert reduced[0].source == "companies_house"
        assert reduced[0].raw_data["cluster_contributor_count"] == 3
        assert len(summaries) == 1

    def test_distinct_leis_stay_separate(self):
        agg = CorporateAggregator()
        records = [
            _corp_record(name="Acme", source="gleif_lei", lei="LEI-AAA"),
            _corp_record(name="Acme", source="gleif_lei", lei="LEI-BBB"),
        ]
        reduced, _ = agg.cluster_observations(records, "Acme")
        assert len(reduced) == 2

    def test_registration_number_fallback_when_no_lei(self):
        agg = CorporateAggregator()
        records = [
            _corp_record(name="Acme Ltd", source="companies_house", reg_no="GB-12345"),
            _corp_record(name="Acme Limited", source="opencorporates", reg_no="GB12345"),
        ]
        # canonical_identifier normalises "GB-12345" and "GB12345" identically.
        reduced, _ = agg.cluster_observations(records, "Acme")
        assert len(reduced) == 1

    def test_registration_number_jurisdiction_scoped(self):
        agg = CorporateAggregator()
        # Same reg number, different jurisdiction -> distinct entities.
        records = [
            _corp_record(name="Acme", source="a", reg_no="12345", jurisdiction="GB"),
            _corp_record(name="Acme", source="b", reg_no="12345", jurisdiction="US-DE"),
        ]
        reduced, _ = agg.cluster_observations(records, "Acme")
        assert len(reduced) == 2

    def test_empty_records_noop(self):
        agg = CorporateAggregator()
        reduced, summaries = agg.cluster_observations([], "Acme")
        assert reduced == []
        assert summaries == []


# ---------------------------------------------------------------------------
# MultiSourceAggregator default hook is a no-op
# ---------------------------------------------------------------------------

class TestDefaultClusterHookIsNoOp:
    def test_base_cluster_observations_returns_unchanged(self):
        # The default hook on the ABC returns (matches, []) — proven via a
        # subclass that doesn't override it.
        agg = CorporateAggregator()
        # Call the BASE implementation explicitly via the MRO.
        from signal_architecture.signals.routing.multi_source import MultiSourceAggregator
        sentinel = [object(), object()]
        reduced, summaries = MultiSourceAggregator.cluster_observations(agg, sentinel, "x")
        assert reduced is sentinel
        assert summaries == []
