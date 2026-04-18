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


# V6/Stage-6 batch 4 — 5 deepened D5 extractors


def test_fema_flood_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import (
        FEMAFloodExtractor,
    )
    sample = {
        "currentVersion": 10.81,
        "spatialReference": {"wkid": 4326, "latestWkid": 4326},
        "layers": [
            {"id": 0, "name": "NFHL Availability"},
            {"id": 1, "name": "Flood Hazard Zones"},
            {"id": 2, "name": "Base Flood Elevations"},
            {"id": 3, "name": "Cross-Sections"},
        ],
    }
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_FEMA_FLOOD", raising=False)

    r = FEMAFloodExtractor().extract("example.com")
    assert r.success is True
    d = r.data
    assert d["nfhl_service_reachable"] is True
    assert d["service_layers"] == 4
    assert d["zone_layer_hits"] == 2
    assert d["current_version"] == 10.81
    assert d["spatial_reference_wkid"] == 4326


def test_usgs_seismic_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import (
        USGSSeismicExtractor,
    )

    def fake_json(url, **kw):
        if "count?" in url and "minmagnitude=5" in url:
            return {"count": 1200}
        if "count?" in url and "minmagnitude=6" in url:
            return {"count": 180}
        if "count?" in url and "minmagnitude=7" in url:
            return {"count": 22}
        if "query?" in url:
            return {
                "features": [
                    {"properties": {
                        "mag": 6.8,
                        "place": "Aleutian Islands",
                        "time": 1700000000000,
                    }},
                ],
            }
        return {}

    monkeypatch.setattr(climate, "_json", fake_json)
    monkeypatch.delenv("DSI_DISABLE_USGS_SEISMIC", raising=False)

    r = USGSSeismicExtractor().extract("example.com")
    assert r.success is True
    d = r.data
    assert d["m5plus_since_2024"] == 1200
    assert d["m6plus_since_2024"] == 180
    assert d["m7plus_since_2024"] == 22
    assert d["most_recent_m6plus"]["mag"] == 6.8
    assert "Aleutian" in d["most_recent_m6plus"]["place"]


def test_tri_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import (
        TRIExtractor,
    )
    sample = [
        {"facility_name": "ACME 1", "state_abbr": "TX",
         "industry_sector": "Chemicals", "trifid": "77001ACME1A"},
        {"facility_name": "ACME 2", "state_abbr": "TX",
         "industry_sector": "Chemicals", "trifid": "77002ACME2B"},
        {"facility_name": "ACME 3", "state_abbr": "LA",
         "industry_sector": "Petroleum", "trifid": "70001ACME3C"},
    ]
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_TRI", raising=False)

    r = TRIExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["facility_count"] == 3
    assert d["state_distribution"]["TX"] == 2
    assert d["state_distribution"]["LA"] == 1
    assert ("Chemicals", 2) in d["industry_top"]
    assert "77001ACME1A" in d["trifid_sample"]


def test_superfund_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import (
        SuperfundExtractor,
    )
    sample = [
        {"state": "CA", "npl_status": "Currently on the Final NPL"},
        {"state": "CA", "npl_status": "Currently on the Final NPL"},
        {"state": "NJ", "npl_status": "Deleted from the Final NPL"},
        {"state": "PA", "npl_status": "Proposed for NPL"},
    ]
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_SUPERFUND", raising=False)

    r = SuperfundExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["probe_ok"] is True
    assert d["sample_size"] == 4
    assert ("CA", 2) in d["state_top"]
    labels = [label for label, _ in d["npl_status_top"]]
    assert any("Final NPL" in l for l in labels)


def test_noaa_cdo_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import NOAACDOExtractor
    sample = {
        "results": [
            {"id": "GHCND", "mindate": "1763-01-01", "maxdate": "2024-12-31"},
            {"id": "GSOM", "mindate": "1763-01-01", "maxdate": "2024-12-31"},
            {"id": "GSOY", "mindate": "1763-01-01", "maxdate": "2024-12-31"},
        ],
    }
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.setenv("NOAA_CDO_TOKEN", "dummy")
    monkeypatch.delenv("DSI_DISABLE_NOAA_CDO", raising=False)
    r = NOAACDOExtractor().extract("example.com")
    d = r.data
    assert d["dataset_count"] == 3
    assert "GHCND" in d["dataset_ids"]
    assert d["mindate"] == "1763-01-01"


def test_usfs_fire_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import USFSFireHazardExtractor
    sample = {
        "currentVersion": 10.81,
        "description": "Wildfire Hazard Potential raster",
        "spatialReference": {"wkid": 4326, "latestWkid": 4326},
        "layers": [
            {"id": 0, "name": "Wildfire Hazard Potential"},
            {"id": 1, "name": "Flame Length Probability"},
        ],
    }
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_USFS_FIRE", raising=False)
    r = USFSFireHazardExtractor().extract("example.com")
    d = r.data
    assert d["service_layers"] == 2
    assert "Wildfire Hazard Potential" in d["layer_names_sample"]
    assert d["spatial_reference_wkid"] == 4326


def test_energystar_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import ENERGYSTARExtractor
    sample = [
        {"primary_property_type": "Office", "state": "CA", "year_certified": "2023"},
        {"primary_property_type": "Office", "state": "CA", "year_certified": "2024"},
        {"primary_property_type": "Hospital", "state": "NY", "year_certified": "2023"},
    ]
    monkeypatch.setattr(climate, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_ENERGYSTAR", raising=False)
    r = ENERGYSTARExtractor().extract("example.com")
    d = r.data
    assert d["building_records_probe"] == 3
    assert ("Office", 2) in d["space_type_top"]
    assert ("CA", 2) in d["state_top"]


def test_nrc_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import climate
    from signal_architecture.signals.extractors.production.climate import (
        NRCInspectionExtractor,
    )
    sample_html = """
    <html>
      <p>Vogtle Nuclear Power Plant, Waynesboro, GA — in operation.</p>
      <p>Three Mile Island Nuclear Power Plant, Middletown, PA — decommissioned.</p>
      <p>Rancho Seco Nuclear Power Plant, Herald, CA — decommissioned.</p>
      <p>Byron Nuclear Power Plant, Byron, IL — in operation.</p>
    </html>
    """
    monkeypatch.setattr(climate, "_text", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_NRC", raising=False)

    r = NRCInspectionExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["reachable"] is True
    assert d["plant_name_mentions"] == 4
    assert d["in_operation_hits"] == 2
    assert d["decommissioned_hits"] == 2
    state_codes = [c for c, _ in d["state_top"]]
    assert "GA" in state_codes
    assert "PA" in state_codes
