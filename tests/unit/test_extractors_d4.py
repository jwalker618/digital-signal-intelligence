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


# V6/Stage-6 deepened-parsing tests — D4 IP extractors.


def test_uspto_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import ip as ipmod
    from signal_architecture.signals.extractors.production.ip import USPTOExtractor
    sample = {
        "total_patent_count": 1250,
        "patents": [
            {"patent_number": "11234567", "patent_date": "2024-09-15"},
            {"patent_number": "11234600", "patent_date": "2024-06-01"},
            {"patent_number": "11100000", "patent_date": "2023-12-01"},
            {"patent_number": "11090000", "patent_date": "2022-01-12"},
        ],
    }
    monkeypatch.setattr(ipmod, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_USPTO", raising=False)
    r = USPTOExtractor().extract("example.com")
    d = r.data
    assert d["patent_count"] == 1250
    assert d["subset_returned"] == 4
    assert d["latest_patent_number"] == "11234567"
    assert d["latest_year"] == "2024"
    assert d["earliest_year"] == "2022"


def test_openalex_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import ip as ipmod
    from signal_architecture.signals.extractors.production.ip import OpenAlexExtractor
    sample = {
        "results": [
            {
                "id": "https://openalex.org/I12345",
                "display_name": "Example University",
                "country_code": "US",
                "type": "education",
                "works_count": 12000,
                "cited_by_count": 450000,
                "summary_stats": {
                    "h_index": 180,
                    "i10_index": 5000,
                    "2yr_mean_citedness": 3.8,
                },
                "x_concepts": [
                    {"display_name": "Biology"},
                    {"display_name": "Medicine"},
                ],
            },
        ],
    }
    monkeypatch.setattr(ipmod, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_OPENALEX", raising=False)
    r = OpenAlexExtractor().extract("example.com")
    d = r.data
    assert d["institution_id"] == "https://openalex.org/I12345"
    assert d["works_count"] == 12000
    assert d["h_index"] == 180
    assert d["type"] == "education"
    concept_names = [c for c, _ in d["concept_top"]]
    assert "Biology" in concept_names


def test_crossref_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import ip as ipmod
    from signal_architecture.signals.extractors.production.ip import CrossRefExtractor
    sample = {
        "message": {
            "total-results": 2500,
            "items": [
                {"publisher": "Elsevier", "type": "journal-article",
                 "issued": {"date-parts": [[2024, 3]]}},
                {"publisher": "Elsevier", "type": "journal-article",
                 "issued": {"date-parts": [[2023, 5]]}},
                {"publisher": "Springer", "type": "book-chapter",
                 "issued": {"date-parts": [[2024, 1]]}},
            ],
        },
    }
    monkeypatch.setattr(ipmod, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_CROSSREF", raising=False)
    r = CrossRefExtractor().extract("example.com")
    d = r.data
    assert d["total_results"] == 2500
    assert ("Elsevier", 2) in d["publisher_top"]
    assert ("journal-article", 2) in d["type_top"]
    assert ("2024", 2) in d["year_top"]


def test_semantic_scholar_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import ip as ipmod
    from signal_architecture.signals.extractors.production.ip import SemanticScholarExtractor
    sample = {
        "total": 9000,
        "data": [
            {"year": 2024, "venue": "NeurIPS", "citationCount": 50},
            {"year": 2024, "venue": "NeurIPS", "citationCount": 120},
            {"year": 2023, "venue": "ICML", "citationCount": 200},
        ],
    }
    monkeypatch.setattr(ipmod, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_SEMANTIC_SCHOLAR", raising=False)
    r = SemanticScholarExtractor().extract("example.com")
    d = r.data
    assert d["paper_total"] == 9000
    assert ("NeurIPS", 2) in d["venue_top"]
    assert d["mean_citation_count"] == (50 + 120 + 200) / 3
    assert d["max_citation_count"] == 200
