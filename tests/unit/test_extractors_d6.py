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


# V6/Stage-6 deepened-parsing tests — D6 sector extractors.


def test_opensky_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import OpenSkyExtractor
    sample = {
        "time": 1700000000,
        "states": [
            ["icao1", "cs1", "United States", 0, 0, 0, 0, 0, False],
            ["icao2", "cs2", "United States", 0, 0, 0, 0, 0, True],
            ["icao3", "cs3", "Germany", 0, 0, 0, 0, 0, False],
            ["icao4", "cs4", "United Kingdom", 0, 0, 0, 0, 0, False],
        ],
    }
    monkeypatch.setattr(sector, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_OPENSKY", raising=False)
    r = OpenSkyExtractor().extract("example.com")
    d = r.data
    assert r.success is True
    assert d["states_returned"] == 4
    assert ("United States", 2) in d["country_top"]
    assert d["on_ground_count"] == 1
    assert d["airborne_count"] == 3


def test_icao_registry_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import ICAORegistryExtractor
    sample = "<html>Doc 7300 Edition 9. Edition 10 pending. Annex 1, Annex 6, Annex 19. file-a.pdf file-b.pdf</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_ICAO", raising=False)
    r = ICAORegistryExtractor().extract("example.com")
    d = r.data
    assert d["edition_hits"] == 2
    assert d["pdf_link_count"] == 2
    assert d["annex_mention_count"] == 3


def test_asias_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import ASIASExtractor
    sample = '<html><h1>ASIAS</h1><h2>Datasets</h2><a href="/a">a</a><a href="/b">b</a> ACAS AIDS Accident Incident</html>'
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_ASIAS", raising=False)
    r = ASIASExtractor().extract("example.com")
    d = r.data
    assert d["heading_count"] == 2
    assert d["dataset_keyword_hits"] == 4
    assert d["internal_link_count"] == 2


def test_ais_hub_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import AISHubExtractor
    sample = [
        {"INFO": "AISHub"},
        [
            {"FLAG": "US", "TYPE": "tanker", "SOG": 10.5},
            {"FLAG": "US", "TYPE": "tanker", "SOG": 8.0},
            {"FLAG": "LR", "TYPE": "container", "SOG": 12.0},
            {"FLAG": "PA", "TYPE": "bulk", "SOG": 0.0},
        ],
    ]
    monkeypatch.setattr(sector, "_json", lambda url, **kw: sample)
    monkeypatch.setenv("AIS_HUB_API_KEY", "dummy")
    monkeypatch.delenv("DSI_DISABLE_AIS_HUB", raising=False)
    r = AISHubExtractor().extract("example.com")
    d = r.data
    assert r.success is True
    assert d["ship_rows_probe"] == 4
    assert ("US", 2) in d["flag_top"]
    assert abs(d["avg_speed_over_ground"] - (10.5 + 8.0 + 12.0 + 0.0) / 4) < 1e-9


def test_marine_cadastre_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import MarineCadastreExtractor
    sample = "<html>2023 2023 2024 AIS download download download UTM Zone 15 EEZ territorial waters</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_MARINE_CADASTRE", raising=False)
    r = MarineCadastreExtractor().extract("example.com")
    d = r.data
    assert d["download_keyword_count"] == 3
    assert ("2023", 2) in d["year_top"]
    assert d["zone_keyword_count"] == 3


def test_emsa_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import EMSAExtractor
    sample = "<html>CO2 emissions reported under MRV. MRV reporting 2022. MRV 2023 2024.</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_EMSA", raising=False)
    r = EMSAExtractor().extract("example.com")
    d = r.data
    assert d["co2_mention_count"] >= 1
    assert d["mrv_mention_count"] == 3


def test_paris_mou_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import ParisMoUExtractor
    sample = '<html>Detention list. detention statistics. white list. grey list. black list.<input name="ship"><input name="imo"></html>'
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_PARIS_MOU", raising=False)
    r = ParisMoUExtractor().extract("example.com")
    d = r.data
    assert d["detention_mention_count"] >= 2
    assert d["performance_list_hits"] == 3
    assert d["search_form_input_count"] == 2


def test_tokyo_mou_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import TokyoMoUExtractor
    sample = "<html>Inspection records. inspection database. detention record. Flag State performance. flag state black list.</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_TOKYO_MOU", raising=False)
    r = TokyoMoUExtractor().extract("example.com")
    d = r.data
    assert d["detention_mention_count"] == 1
    assert d["inspection_mention_count"] == 2
    assert d["flag_state_mention_count"] == 2


def test_phmsa_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import PHMSAExtractor
    sample = "<html>2023 2024. hazmat incidents. natural gas pipelines. hazardous liquid incidents. Download data.csv and incidents.xlsx.</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_PHMSA", raising=False)
    r = PHMSAExtractor().extract("example.com")
    d = r.data
    assert d["hazmat_mention_count"] == 1
    assert d["gas_mention_count"] == 1
    assert d["liquid_mention_count"] == 1
    assert d["dataset_link_count"] == 2


def test_bsee_detail_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import BSEEDetailExtractor
    sample = '<html>INJURY reported 2023. FATALITY 2022. FIRE incident. <a href="/r1">r</a> <a href="/r2">r</a></html>'
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_BSEE", raising=False)
    r = BSEEDetailExtractor().extract("example.com")
    d = r.data
    severity_dict = dict(d["severity_top"])
    assert severity_dict.get("INJURY") == 1
    assert severity_dict.get("FATALITY") == 1
    assert d["link_count"] == 2


def test_nerc_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sector
    from signal_architecture.signals.extractors.production.sector import NERCVioExtractor
    sample = "<html>CIP-007, CIP-010 breaches. BAL-002 violation. Penalty $ 125,000. $ 1,500,000 to respondent.</html>"
    monkeypatch.setattr(sector, "_text", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_NERC", raising=False)
    r = NERCVioExtractor().extract("example.com")
    d = r.data
    standards = dict(d["standard_top"])
    assert standards.get("CIP") == 2
    assert standards.get("BAL") == 1
    assert d["penalty_sum_usd"] == 1625000.0
