"""V6/D1 — smoke tests for Universal Web Footprint extractors.

These tests cover the D1 contract (SOURCE_NAME, COST_TIER, kill-switch,
API-key gating) plus the registry wiring. Live HTTP calls are not made —
each extractor is exercised through the kill-switch / missing-key code
paths so the framework-runs-without-credentials guarantee is verified
without hitting external services.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d1_extractors_registered(factory_module):
    expected_web = {
        "web.github_org", "web.wayback", "web.urlscan", "web.commoncrawl",
        "web.tranco", "web.safebrowsing", "web.phishtank", "web.openphish",
        "web.cloudflare_radar", "web.google_transparency",
    }
    expected_identity = {"identity.hibp", "identity.intelx"}
    expected_sentiment = {
        "sentiment.trustpilot", "sentiment.bbb", "sentiment.glassdoor",
        "sentiment.google_reviews",
    }
    reg = factory_module._registry.list_extractors()
    names = set(reg.keys())
    missing = (expected_web | expected_identity | expected_sentiment) - names
    assert not missing, f"missing D1 extractors in registry: {sorted(missing)}"


def test_kill_switch_returns_neutral_absence(monkeypatch):
    from signal_architecture.signals.extractors.production.web import WaybackExtractor
    monkeypatch.setenv("DSI_DISABLE_WAYBACK", "true")
    extractor = WaybackExtractor()
    result = extractor.extract("example.com")
    assert result.success is False
    assert result.metadata["confidence"] == 0.0
    assert result.metadata["absence_reason"] == "kill_switch_active"
    assert result.source.endswith(":absent")


def test_missing_api_key_returns_neutral_absence(monkeypatch):
    from signal_architecture.signals.extractors.production.web import (
        GoogleSafeBrowsingExtractor,
    )
    monkeypatch.delenv("GOOGLE_SAFEBROWSING_API_KEY", raising=False)
    monkeypatch.delenv("DSI_DISABLE_SAFEBROWSING", raising=False)
    result = GoogleSafeBrowsingExtractor().extract("example.com")
    assert result.success is False
    assert result.metadata["confidence"] == 0.0
    assert result.metadata["absence_reason"] == "api_key_missing"


def test_cost_tier_rank_ordering():
    from signal_architecture.signals.extractors.production.web import (
        WaybackExtractor,  # free
    )
    from signal_architecture.signals.extractors.production.identity import (
        HIBPExtractor,    # low
        IntelXExtractor,  # medium
    )
    ranks = [
        WaybackExtractor.cost_tier_rank(),
        HIBPExtractor.cost_tier_rank(),
        IntelXExtractor.cost_tier_rank(),
    ]
    assert ranks == sorted(ranks)


def test_absence_result_short_ttl():
    from signal_architecture.signals.extractors.production.identity import HIBPExtractor
    import os
    os.environ.pop("HIBP_API_KEY", None)
    result = HIBPExtractor().extract("example.com")
    assert result.success is False
    # Short TTL (5m) so ops can re-enable the source without waiting for
    # a stale cache entry to expire.
    assert result.ttl_seconds == 300
