"""V6/D6 — sector-telemetry extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


EXPECTED_D6 = {
    "sector.opensky", "sector.icao_registry", "sector.asias",
    "sector.ais_hub", "sector.marine_cadastre", "sector.emsa_thetis",
    "sector.paris_mou", "sector.tokyo_mou",
    "sector.phmsa", "sector.bsee_detail", "sector.nerc_violations",
}


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d6_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D6 - set(reg)
    assert not missing


def test_ais_hub_is_low_cost_and_api_key_gated():
    from signal_architecture.signals.extractors.production.sector import AISHubExtractor
    assert AISHubExtractor.COST_TIER == "low"
    assert AISHubExtractor.API_KEY_ENV == "AIS_HUB_API_KEY"


def test_ais_hub_without_key(monkeypatch):
    from signal_architecture.signals.extractors.production.sector import AISHubExtractor
    monkeypatch.delenv("AIS_HUB_API_KEY", raising=False)
    monkeypatch.delenv("DSI_DISABLE_AIS_HUB", raising=False)
    result = AISHubExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "api_key_missing"


def test_opensky_kill_switch(monkeypatch):
    from signal_architecture.signals.extractors.production.sector import OpenSkyExtractor
    monkeypatch.setenv("DSI_DISABLE_OPENSKY", "true")
    result = OpenSkyExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "kill_switch_active"
