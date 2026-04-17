"""V6/D3 — Litigation / regulatory extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


EXPECTED_D3 = {
    "litigation.courtlistener",
    "litigation.pacer_rss",
    "litigation.stanford_scac",
    "litigation.sec_litreleases",
    "litigation.finra_brokercheck",
    "litigation.sec_iapd",
    "litigation.gdpr_tracker",
    "litigation.cms_hospital",
    "litigation.joint_commission",
    "litigation.npdb_public",
    "litigation.pcaob",
    "litigation.osha",
    "litigation.fmcsa",
    "litigation.nhtsa_recalls",
    "litigation.cpsc_recalls",
    "litigation.fda_recalls",
    "litigation.eu_safety_gate",
    "litigation.usda_fsis",
}


def test_all_d3_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D3 - set(reg)
    assert not missing, f"missing D3 extractors: {sorted(missing)}"


def test_all_d3_are_free_tier():
    """Every D3 source is free per the plan (some need optional tokens)."""
    from signal_architecture.signals.extractors.production import litigation
    for name in EXPECTED_D3:
        cls_attr = name.split(".")[-1]
        # Convert snake to class name lookup via module listing.
    # Use the module's __dict__ — every D3 class inherits _LitigationBase.
    classes = [
        cls for cls in litigation.__dict__.values()
        if isinstance(cls, type)
        and issubclass(cls, litigation._LitigationBase)
        and cls is not litigation._LitigationBase
    ]
    assert len(classes) == 18, f"expected 18 D3 extractors, found {len(classes)}"
    for cls in classes:
        assert cls.COST_TIER == "free", f"{cls.__name__} is not free-tier"


def test_kill_switch_blocks_request(monkeypatch):
    from signal_architecture.signals.extractors.production.litigation import (
        CourtListenerExtractor,
    )
    monkeypatch.setenv("DSI_DISABLE_COURTLISTENER", "true")
    result = CourtListenerExtractor().extract("example.com")
    assert result.success is False
    assert result.metadata["absence_reason"] == "kill_switch_active"


# ---------------------------------------------------------------------------
# V6/Stage-6 field-depth tests
#
# Each test monkeypatches the fetch helper in `litigation` to return a
# canned payload; the goal is to exercise the deepened parsing logic
# without making live HTTP calls.
# ---------------------------------------------------------------------------


def test_courtlistener_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        CourtListenerExtractor,
    )

    sample = {
        "count": 42,
        "results": [
            {"absolute_url": "/opinion/1/", "court": "ca9",
             "dateFiled": "2024-03-10", "nature_of_suit": "470",
             "status": "Pending"},
            {"absolute_url": "/opinion/2/", "court": "ca9",
             "dateFiled": "2023-06-01", "nature_of_suit": "470",
             "status": "Terminated"},
            {"absolute_url": "/opinion/3/", "court": "scotus",
             "dateFiled": "2024-01-15", "nature_of_suit": "890",
             "status": "pending"},
        ],
    }
    monkeypatch.setattr(litigation, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_COURTLISTENER", raising=False)
    monkeypatch.setenv("COURTLISTENER_TOKEN", "test-token")

    result = CourtListenerExtractor().extract("example.com")
    assert result.success is True
    data = result.data
    assert data["total_hits"] == 42
    assert data["result_count"] == 3
    assert data["pending_case_count"] == 2
    assert ("ca9", 2) in data["courts_top"]
    assert "2024" in data["filing_year_histogram"]
    assert data["filing_year_histogram"]["2024"] == 2


def test_osha_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        OSHAEstablishmentExtractor,
    )

    sample_html = """
    <table>
      <tr><th>Activity Nr</th><th>Name</th><th>Open Date</th><th>Scope</th><th>Violations</th><th>Initial Penalty</th></tr>
      <tr><td>1234567</td><td>Example LLC</td><td>03/15/2024</td><td>Partial</td><td>SERIOUS: 2</td><td>$12,500</td></tr>
      <tr><td>7654321</td><td>Example LLC</td><td>06/10/2023</td><td>Comprehensive</td><td>OTHER: 1</td><td>$500</td></tr>
    </table>
    """
    monkeypatch.setattr(litigation, "_text", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_OSHA", raising=False)

    result = OSHAEstablishmentExtractor().extract("example.com")
    assert result.success is True
    d = result.data
    assert d["inspection_count"] == 2
    assert d["serious_violation_rows"] == 1
    assert d["total_initial_penalty_usd"] == 13000.0
    assert d["most_recent_inspection"] == "03/15/2024"
    assert len(d["inspection_rows_sample"]) == 2


def test_fmcsa_deepened_parsing_with_dot_number(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        FMCSASMSExtractor,
    )

    sample = {
        "content": {
            "carrier": {
                "legalName": "ACME TRUCKING INC",
                "dbaName": "ACME",
                "statusCode": "A",
                "allowedToOperate": "Y",
                "totalDrivers": 250,
                "totalPowerUnits": 180,
                "crashTotal": 4,
                "fatalCrash": 0,
                "injCrash": 3,
                "towawayCrash": 1,
                "vehicleInsp": 100,
                "driverInsp": 80,
                "hazmatInsp": 10,
                "iepInsp": 0,
                "vehicleOosInsp": 12,
                "driverOosInsp": 6,
                "hazmatOosInsp": 0,
                "iepOosInsp": 0,
            },
        },
    }
    monkeypatch.setattr(litigation, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_FMCSA", raising=False)

    result = FMCSASMSExtractor().extract("USDOT-123456")
    assert result.success is True
    d = result.data
    assert d["dot_number"] == "123456"
    assert d["legal_name"] == "ACME TRUCKING INC"
    assert d["operating_status"] == "A"
    assert d["inspections_total"] == 190
    assert d["oos_total"] == 18
    # extractor rounds oos_rate to 4 decimals
    assert abs(d["oos_rate"] - round(18 / 190, 4)) < 1e-9
    assert d["crash_total"] == 4


def test_fmcsa_fallback_when_no_dot(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        FMCSASMSExtractor,
    )

    sample_html = "<html>ACME not found</html>"
    monkeypatch.setattr(litigation, "_text", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_FMCSA", raising=False)

    result = FMCSASMSExtractor().extract("acme.com")
    assert result.success is True
    assert result.data["endpoint_reachable"] is True
    assert result.data["sms_basic_score_endpoint_reachable"] is True


# V6/Stage-6 batch 2 — 5 more deepened D3 extractors


def test_stanford_scac_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        StanfordSCACExtractor,
    )
    sample_html = """
    <table>
      <tr><th>Date</th><th>Company</th><th>Outcome</th></tr>
      <tr><td>2024-03-15</td><td>Acme</td><td>Settled for $12M</td></tr>
      <tr><td>2023-08-10</td><td>Acme</td><td>Dismissed with prejudice</td></tr>
      <tr><td>2024-11-02</td><td>Acme</td><td>Pending — motion filed</td></tr>
    </table>
    """
    monkeypatch.setattr(litigation, "_text", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_SCAC", raising=False)

    r = StanfordSCACExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["filing_count"] == 3
    assert d["outcome_breakdown"]["settled"] == 1
    assert d["outcome_breakdown"]["dismissed"] == 1
    assert d["outcome_breakdown"]["pending"] == 1
    assert d["most_recent_filing"] == "2024-11-02"
    assert d["first_filed"] == "2023-08-10"


def test_finra_brokercheck_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        FINRABrokerCheckExtractor,
    )
    sample = {
        "hits": {
            "hits": [
                {"_source": {"firm_name": "ACME FINANCIAL",
                             "firm_source_id": "12345",
                             "firm_disclosure_count": 3}},
                {"_source": {"firm_name": "ACME WEALTH",
                             "firm_source_id": "67890",
                             "firm_disclosure_count": 1}},
            ],
        },
    }
    monkeypatch.setattr(litigation, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_FINRA", raising=False)

    r = FINRABrokerCheckExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["firm_hits"] == 2
    assert "ACME FINANCIAL" in d["firm_names_top"]
    assert "12345" in d["crd_numbers_top"]
    assert d["total_disclosures_hit"] == 4


def test_nhtsa_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        NHTSARecallsExtractor,
    )
    call_counts = {"n": 0}

    def fake_json(url, **kw):
        call_counts["n"] += 1
        return {
            "Count": 2,
            "results": [
                {"NHTSACampaignNumber": f"24V{call_counts['n']:03d}",
                 "Component": "ELECTRICAL: BATTERY",
                 "Consequence": "Battery may short-circuit. This can cause a fire."},
                {"NHTSACampaignNumber": f"24V{call_counts['n']:03d}A",
                 "Component": "AIR BAGS: FRONTAL",
                 "Consequence": "Airbag may not deploy."},
            ],
        }
    monkeypatch.setattr(litigation, "_json", fake_json)
    monkeypatch.delenv("DSI_DISABLE_NHTSA", raising=False)

    r = NHTSARecallsExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["recall_count"] == 6  # 2 per year × 3 years
    assert 2024 in d["recalls_per_year"]
    assert 2023 in d["recalls_per_year"]
    assert 2022 in d["recalls_per_year"]
    # ELECTRICAL + AIR BAGS should both appear in top-5
    component_names = [c for c, _ in d["component_top"]]
    assert "ELECTRICAL" in component_names
    assert "AIR BAGS" in component_names
    assert len(d["nhtsa_campaign_ids_sample"]) >= 6


def test_cpsc_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        CPSCRecallsExtractor,
    )
    sample = [
        {
            "Hazards": [{"Name": "Fire Hazard"}],
            "Products": [{"Type": "Power Tools"}],
            "Injuries": [{"Count": 3}],
            "NumberOfDeaths": 0,
            "NumberOfUnits": "12,500",
            "RecallDate": "2024-05-10",
        },
        {
            "Hazards": [{"Name": "Fire Hazard"}, {"Name": "Burn Hazard"}],
            "Products": [{"Type": "Power Tools"}],
            "Injuries": [],
            "NumberOfDeaths": 1,
            "NumberOfUnits": "5000",
            "RecallDate": "2023-11-22",
        },
    ]
    monkeypatch.setattr(litigation, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_CPSC", raising=False)

    r = CPSCRecallsExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["result_count"] == 2
    assert dict(d["hazard_top"])["Fire Hazard"] == 2
    assert d["injuries_total"] == 3
    assert d["deaths_total"] == 1
    assert d["units_recalled_total"] == 17500
    assert d["most_recent_recall"] == "2024-05-10"


def test_fda_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import litigation
    from signal_architecture.signals.extractors.production.litigation import (
        FDARecallsExtractor,
    )
    sample = {
        "meta": {"results": {"total": 42}},
        "results": [
            {"classification": "Class I",
             "recall_initiation_date": "20240310",
             "distribution_pattern": "Nationwide — all 50 states"},
            {"classification": "Class II",
             "recall_initiation_date": "20231105",
             "distribution_pattern": "Nationwide — all 50 states"},
            {"classification": "Class I",
             "recall_initiation_date": "20240902",
             "distribution_pattern": "Texas, Oklahoma, Louisiana only"},
        ],
    }
    monkeypatch.setattr(litigation, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_FDA", raising=False)

    r = FDARecallsExtractor().extract("acme.com")
    assert r.success is True
    d = r.data
    assert d["enforcement_hits"] == 42
    assert d["classification_breakdown"]["Class I"] == 2
    assert d["classification_breakdown"]["Class II"] == 1
    assert "2024" in d["recalls_per_year"]
    assert d["recalls_per_year"]["2024"] == 2
    assert d["result_sample_count"] == 3
