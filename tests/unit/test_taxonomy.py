"""V6/E9 — canonical taxonomy tests."""
from __future__ import annotations

import pytest

from signal_architecture.signals.taxonomy import (
    CANONICAL_CATEGORIES,
    CANONICAL_IDS,
    CANONICAL_ID_TO_NAME,
    is_canonical,
    require_canonical,
)


def test_exactly_seven_canonical_categories():
    assert len(CANONICAL_CATEGORIES) == 7
    assert len(CANONICAL_IDS) == 7


def test_expected_ids():
    assert CANONICAL_IDS == {
        "network_authority",
        "technical_infrastructure",
        "corporate_footprint",
        "behavioural",
        "public_record",
        "structured_data",
        "direct_inquiry",
    }


def test_is_canonical_roundtrip():
    for cat in CANONICAL_CATEGORIES:
        assert is_canonical(cat.id)
        assert CANONICAL_ID_TO_NAME[cat.id] == cat.name


def test_non_canonical_returns_false():
    assert not is_canonical("operational_quality")
    assert not is_canonical("safety_record")
    assert not is_canonical("")


def test_require_canonical_raises_on_bad_id():
    with pytest.raises(ValueError):
        require_canonical("made_up_category")


def test_require_canonical_accepts_each_valid_id():
    for cat in CANONICAL_CATEGORIES:
        require_canonical(cat.id)
