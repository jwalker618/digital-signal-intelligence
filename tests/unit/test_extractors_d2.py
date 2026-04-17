"""V6/D2 — technical/infrastructure extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


EXPECTED_D2 = {
    "stack.shodan",
    "stack.censys",
    "stack.bgp_ripestat",
    "stack.peeringdb",
    "stack.wappalyzer",
    "stack.builtwith",
    "stack.httparchive",
}


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d2_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D2 - set(reg)
    assert not missing, f"missing D2 extractors: {sorted(missing)}"


def test_shodan_kill_switch(monkeypatch):
    from signal_architecture.signals.extractors.production.stack import ShodanExtractor
    monkeypatch.setenv("DSI_DISABLE_SHODAN", "true")
    result = ShodanExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "kill_switch_active"


def test_builtwith_requires_api_key(monkeypatch):
    from signal_architecture.signals.extractors.production.stack import BuiltWithExtractor
    monkeypatch.delenv("BUILTWITH_API_KEY", raising=False)
    monkeypatch.delenv("DSI_DISABLE_BUILTWITH", raising=False)
    result = BuiltWithExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "api_key_missing"


def test_wappalyzer_is_free_and_no_api_key():
    from signal_architecture.signals.extractors.production.stack import WappalyzerExtractor
    assert WappalyzerExtractor.COST_TIER == "free"
    assert WappalyzerExtractor.API_KEY_ENV is None


def test_cost_tier_ordering():
    from signal_architecture.signals.extractors.production.stack import (
        BGPExtractor, ShodanExtractor, CensysExtractor,
    )
    # free < low < medium
    assert BGPExtractor.cost_tier_rank() < ShodanExtractor.cost_tier_rank()
    assert ShodanExtractor.cost_tier_rank() < CensysExtractor.cost_tier_rank()
