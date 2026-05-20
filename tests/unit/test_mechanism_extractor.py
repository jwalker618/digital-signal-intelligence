"""V7 Phase 12 — extractor: eligibility, scrubber, JSON parsing."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from signal_architecture.mechanism import extract_mechanism, is_eligible
from signal_architecture.mechanism.extractor import _strip_disallowed
from signal_architecture.signals.types import SignalResult


def _sig(
    grade="structured_attested",
    repro="stable",
    cluster_id="C1",
    deterministic=True,
    primitive="governance",
):
    md = {}
    if cluster_id:
        md["cluster_id"] = cluster_id
        md["deterministic"] = deterministic
    return SignalResult(
        signal_id="director_litigation",
        score=80.0,
        confidence=0.85,
        evidence_grade=grade,
        evidence_basis="multi-source corroboration",
        reproducibility=repro,
        primitive_type=primitive,
        metadata=md,
    )


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

class TestEligibility:
    def test_happy_path(self):
        assert is_eligible(_sig(), validator_advanced=True) is True

    def test_not_advanced_blocks(self):
        assert is_eligible(_sig(), validator_advanced=False) is False

    def test_below_grade_blocks(self):
        assert is_eligible(_sig(grade="corroborated"), validator_advanced=True) is False
        assert is_eligible(_sig(grade="observed"), validator_advanced=True) is False

    def test_behaviourally_validated_accepted(self):
        assert is_eligible(
            _sig(grade="behaviourally_validated"), validator_advanced=True,
        ) is True

    def test_non_stable_repro_blocks(self):
        assert is_eligible(_sig(repro="flaky"), validator_advanced=True) is False
        assert is_eligible(_sig(repro="unstable"), validator_advanced=True) is False
        assert is_eligible(_sig(repro="unknown"), validator_advanced=True) is False
        assert is_eligible(_sig(repro=None), validator_advanced=True) is False

    def test_no_cluster_blocks(self):
        assert is_eligible(_sig(cluster_id=None), validator_advanced=True) is False

    def test_non_deterministic_cluster_blocks(self):
        assert is_eligible(_sig(deterministic=False), validator_advanced=True) is False


# ---------------------------------------------------------------------------
# Scrubber
# ---------------------------------------------------------------------------

class TestScrubber:
    def test_strips_years(self):
        out = _strip_disallowed("Filed in 2024 with regulator")
        assert "2024" not in out
        assert "<year>" in out

    def test_strips_proper_nouns(self):
        out = _strip_disallowed("John Smith was director at Acme Corporation")
        assert "John Smith" not in out
        # "Acme Corporation" also matches the 2-word title-case pattern.
        assert "<name>" in out

    def test_strips_all_caps_acronyms(self):
        out = _strip_disallowed("Listed on OFAC SDN and NACHA")
        assert "OFAC" not in out
        assert "SDN" not in out
        assert "NACHA" not in out
        assert "<acronym>" in out

    def test_empty_input(self):
        assert _strip_disallowed("") == ""
        assert _strip_disallowed(None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# extract_mechanism
# ---------------------------------------------------------------------------

def _llm_returning(data: dict):
    return MagicMock(return_value=json.dumps(data))


class TestExtractMechanism:
    def test_well_formed_response_builds_mechanism(self):
        llm = _llm_returning({
            "summary": "Entity has board overlap with sanctioned counterparty",
            "tags": ["board_overlap", "sanctions"],
            "keywords": ["board", "overlap", "sanctions"],
            "what_made_it_high_grade": "Two registers + court agreement",
        })
        m = extract_mechanism(
            llm, _sig(),
            sector_tags=["fi", "do"], cycle_id="mv-42",
        )
        assert m is not None
        assert m.primitive_type == "governance"
        assert m.source_cluster_id == "C1"
        assert m.source_signal_id == "director_litigation"
        assert m.source_cycle_id == "mv-42"
        assert m.sector_tags == ["fi", "do"]
        assert "board_overlap" in m.tags
        assert m.id.startswith("mech-")

    def test_response_summary_scrubbed(self):
        # LLM violation — includes a year + name. Scrubber catches both.
        llm = _llm_returning({
            "summary": "Listed in 2024 by OFAC; John Smith named",
            "tags": ["sdn"],
            "keywords": ["sdn"],
            "what_made_it_high_grade": "x",
        })
        m = extract_mechanism(
            llm, _sig(), sector_tags=["fi"], cycle_id="mv-1",
        )
        assert m is not None
        assert "2024" not in m.summary
        assert "John Smith" not in m.summary

    def test_empty_summary_returns_none(self):
        llm = _llm_returning({
            "summary": "",
            "tags": [],
            "keywords": [],
            "what_made_it_high_grade": "x",
        })
        assert extract_mechanism(llm, _sig(), sector_tags=[], cycle_id="mv") is None

    def test_unparseable_json_returns_none(self):
        llm = MagicMock(return_value="this is not JSON")
        assert extract_mechanism(llm, _sig(), sector_tags=[], cycle_id="mv") is None

    def test_llm_exception_returns_none(self):
        def boom(*, system, user):
            raise RuntimeError("network")
        assert extract_mechanism(boom, _sig(), sector_tags=[], cycle_id="mv") is None

    def test_non_string_tags_filtered(self):
        llm = _llm_returning({
            "summary": "abstract pattern",
            "tags": ["good_tag", 42, None, {"x": 1}],
            "keywords": [],
            "what_made_it_high_grade": "",
        })
        m = extract_mechanism(llm, _sig(), sector_tags=[], cycle_id="mv")
        assert m is not None
        assert m.tags == ["good_tag"]
