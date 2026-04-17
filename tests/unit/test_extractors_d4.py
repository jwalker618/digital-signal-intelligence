"""V6/D4 — IP / innovation extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


EXPECTED_D4 = {
    "ip.uspto",
    "ip.epo_ops",
    "ip.openalex",
    "ip.crossref",
    "ip.semantic_scholar",
}


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d4_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D4 - set(reg)
    assert not missing


def test_all_d4_are_free():
    from signal_architecture.signals.extractors.production import ip as ip_mod
    classes = [
        cls for cls in ip_mod.__dict__.values()
        if isinstance(cls, type)
        and issubclass(cls, ip_mod._IPBase)
        and cls is not ip_mod._IPBase
    ]
    assert len(classes) == 5
    for cls in classes:
        assert cls.COST_TIER == "free"


def test_uspto_kill_switch(monkeypatch):
    from signal_architecture.signals.extractors.production.ip import USPTOExtractor
    monkeypatch.setenv("DSI_DISABLE_USPTO", "true")
    result = USPTOExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "kill_switch_active"


def test_semantic_scholar_works_without_key(monkeypatch):
    """Semantic Scholar allows anonymous calls — API_KEY_ENV is None."""
    from signal_architecture.signals.extractors.production.ip import (
        SemanticScholarExtractor,
    )
    assert SemanticScholarExtractor.API_KEY_ENV is None
    assert SemanticScholarExtractor.has_api_key() is True
