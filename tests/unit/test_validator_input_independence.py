"""V7 Phase 6 — ValidatorInput independence: the validator must NOT see
raw_data, metadata, reasoning, or any field outside the whitelist.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.types import SignalResult
from signal_architecture.validation.types import ValidatorInput


def _base_kwargs():
    return dict(
        signal_id="x",
        confidence=1.0,
        evidence_grade="observed",
        evidence_basis="basis",
        entity_id="e",
        entity_name="E",
        coverage="cyber",
    )


class TestExtraForbidden:
    def test_rejects_raw_data(self):
        with pytest.raises(ValidationError):
            ValidatorInput(**_base_kwargs(), raw_data={"x": 1})  # type: ignore[call-arg]

    def test_rejects_metadata(self):
        with pytest.raises(ValidationError):
            ValidatorInput(**_base_kwargs(), metadata={"x": 1})  # type: ignore[call-arg]

    def test_rejects_reasoning(self):
        with pytest.raises(ValidationError):
            ValidatorInput(**_base_kwargs(), reasoning="chain of thought")  # type: ignore[call-arg]

    def test_rejects_transcript(self):
        with pytest.raises(ValidationError):
            ValidatorInput(**_base_kwargs(), transcript="LLM transcript")  # type: ignore[call-arg]

    def test_rejects_underscore_prefixed(self):
        with pytest.raises(ValidationError):
            ValidatorInput(**_base_kwargs(), _private="x")  # type: ignore[call-arg]


class TestFromSignalStrips:
    def test_strips_metadata_and_raw_data(self):
        sig = SignalResult(
            signal_id="x",
            score=50.0,
            confidence=1.0,
            evidence_grade="observed",
            evidence_basis="basis",
            raw_data={"secret_transcript": "..."},
            metadata={"chain_of_thought": "..."},
        )
        vi = ValidatorInput.from_signal(
            sig, entity_id="e", entity_name="E",
            entity_country="UK", coverage="cyber",
        )
        payload = vi.model_dump()
        assert "raw_data" not in payload
        assert "metadata" not in payload
        # And the actual content never makes it into the dump
        assert "secret_transcript" not in str(payload)
        assert "chain_of_thought" not in str(payload)

    def test_serialises_sources_as_dicts(self):
        src = EvidenceSource(
            source_id="ofac", kind="register",
            ref="https://example.com/ofac",
            fetched_at=datetime.now(timezone.utc),
        )
        sig = SignalResult(
            signal_id="x", score=50, confidence=1.0,
            evidence_grade="observed", evidence_basis="b",
            evidence_sources=[src],
        )
        vi = ValidatorInput.from_signal(
            sig, entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert len(vi.evidence_sources) == 1
        assert vi.evidence_sources[0]["source_id"] == "ofac"

    def test_absence_sub_type_carried_through(self):
        sig = SignalResult(
            signal_id="x", score=95.0, confidence=1.0,
            evidence_grade="structured_attested", evidence_basis="ofac clean",
            absence_sub_type="absence_authoritative_empty",
        )
        vi = ValidatorInput.from_signal(
            sig, entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert vi.absence_sub_type == "absence_authoritative_empty"


class TestImmutability:
    def test_frozen(self):
        vi = ValidatorInput(**_base_kwargs())
        with pytest.raises(ValidationError):
            vi.signal_id = "y"  # type: ignore[misc]
