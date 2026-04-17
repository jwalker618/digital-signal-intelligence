"""V6/D8 — SignalBrokerV2 tests."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from signal_architecture.signals.routing.source_router import (
    COST_TIER_USD,
    SignalBrokerV2,
    SourceSelection,
)


@dataclass
class _FakeResult:
    success: bool
    metadata: Dict[str, Any]


class _FakeExtractorBase:
    SOURCE_NAME = "fake"
    COST_TIER = "free"

    @classmethod
    def cost_tier_rank(cls) -> int:
        return {"free": 0, "low": 1, "medium": 2, "high": 3}[cls.COST_TIER]

    @classmethod
    def is_disabled(cls) -> bool:
        return bool(os.environ.get(f"DSI_DISABLE_{cls.SOURCE_NAME.upper()}"))

    @classmethod
    def has_api_key(cls) -> bool:
        return True

    def extract(self, entity_id, context=None):  # noqa: ANN001
        return _FakeResult(success=True, metadata={"confidence": 0.9})


class FreeExtractor(_FakeExtractorBase):
    SOURCE_NAME = "free_source"
    COST_TIER = "free"


class PaidExtractor(_FakeExtractorBase):
    SOURCE_NAME = "paid_source"
    COST_TIER = "medium"


class LowConfidenceExtractor(_FakeExtractorBase):
    SOURCE_NAME = "low_conf"
    COST_TIER = "free"

    def extract(self, entity_id, context=None):
        return _FakeResult(success=True, metadata={"confidence": 0.3})


class DisabledExtractor(_FakeExtractorBase):
    SOURCE_NAME = "disabled_source"
    COST_TIER = "free"

    @classmethod
    def is_disabled(cls):
        return True


def _lookup(extractors):
    def fn(signal_id):
        return extractors
    return fn


def test_broker_picks_cheapest_satisfying_source():
    broker = SignalBrokerV2(candidate_lookup=_lookup([PaidExtractor, FreeExtractor]))
    sel = broker.extract("stack_fingerprint", "acme")
    assert sel.selected_source == "free_source"
    assert sel.cost_tier == "free"
    assert sel.cost_usd_estimate == 0.0


def test_broker_skips_low_confidence():
    broker = SignalBrokerV2(
        candidate_lookup=_lookup([LowConfidenceExtractor, PaidExtractor]),
        min_confidence=0.6,
    )
    sel = broker.extract("technology_stack", "acme")
    assert sel.selected_source == "paid_source"
    assert sel.confidence >= 0.6
    # Low-conf source was tried before paid
    assert "low_conf" in sel.tried_sources


def test_broker_skips_disabled():
    broker = SignalBrokerV2(candidate_lookup=_lookup([DisabledExtractor, FreeExtractor]))
    sel = broker.extract("technology_stack", "acme")
    assert sel.selected_source == "free_source"


def test_broker_preferred_source_wins_when_satisfying():
    broker = SignalBrokerV2(candidate_lookup=_lookup([FreeExtractor, PaidExtractor]))
    sel = broker.extract("technology_stack", "acme", preferred_source="paid_source")
    assert sel.selected_source == "paid_source"


def test_broker_returns_none_when_no_source_available():
    broker = SignalBrokerV2(candidate_lookup=_lookup([LowConfidenceExtractor]))
    sel = broker.extract("technology_stack", "acme", min_confidence=0.9)
    assert sel.selected_source is None
    assert sel.reason == "no source met minimum confidence"


def test_cost_tier_usd_known_values():
    assert COST_TIER_USD["free"] == 0.0
    assert COST_TIER_USD["high"] > COST_TIER_USD["medium"] > COST_TIER_USD["low"]
