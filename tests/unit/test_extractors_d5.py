"""V6/D5 — climate/environment extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


EXPECTED_D5 = {
    "climate.fema_flood",
    "climate.noaa_cdo",
    "climate.usfs_fire_hazard",
    "climate.usgs_seismic",
    "climate.copernicus_sentinel",
    "climate.ecmwf_era5",
    "climate.cdp_open",
    "climate.energystar",
    "climate.epa_tri",
    "climate.epa_superfund",
    "climate.nrc_inspections",
}


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d5_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D5 - set(reg)
    assert not missing


def test_all_d5_are_free():
    from signal_architecture.signals.extractors.production import climate
    classes = [
        cls for cls in climate.__dict__.values()
        if isinstance(cls, type)
        and issubclass(cls, climate._ClimateBase)
        and cls is not climate._ClimateBase
    ]
    assert len(classes) == 11
    for cls in classes:
        assert cls.COST_TIER == "free"


def test_noaa_without_token(monkeypatch):
    from signal_architecture.signals.extractors.production.climate import NOAACDOExtractor
    monkeypatch.delenv("NOAA_CDO_TOKEN", raising=False)
    monkeypatch.delenv("DSI_DISABLE_NOAA_CDO", raising=False)
    result = NOAACDOExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "api_key_missing"


def test_fema_kill_switch(monkeypatch):
    from signal_architecture.signals.extractors.production.climate import FEMAFloodExtractor
    monkeypatch.setenv("DSI_DISABLE_FEMA_FLOOD", "true")
    result = FEMAFloodExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "kill_switch_active"
