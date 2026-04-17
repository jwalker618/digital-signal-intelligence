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
