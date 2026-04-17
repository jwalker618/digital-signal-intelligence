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


# V6/Stage-6 deepened-parsing tests — D1 web extractors.


def test_github_org_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import GitHubOrgExtractor
    sample = {
        "public_repos": 142,
        "public_gists": 3,
        "followers": 5100,
        "following": 0,
        "created_at": "2015-06-15T12:34:56Z",
        "updated_at": "2024-01-10T10:00:00Z",
        "email": "ops@example.com",
        "blog": "https://example.com",
        "location": "San Francisco",
        "company": "@example",
        "is_verified": True,
    }
    monkeypatch.setattr(web, "_json_get", lambda url, **kw: sample)
    monkeypatch.setenv("GITHUB_PAT", "dummy")
    monkeypatch.delenv("DSI_DISABLE_GITHUB_ORG", raising=False)
    r = GitHubOrgExtractor().extract("example.com")
    d = r.data
    assert d["public_repos"] == 142
    assert d["public_gists"] == 3
    assert d["era_band"] == "2010s"
    assert d["is_verified"] is True
    assert d["location"] == "San Francisco"


def test_wayback_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import WaybackExtractor
    sample = [
        ["timestamp"],
        ["20101010000000"],
        ["20130315010000"],
        ["20130815010000"],
        ["20200101000000"],
        ["20240101000000"],
    ]
    monkeypatch.setattr(web, "_json_get", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_WAYBACK", raising=False)
    r = WaybackExtractor().extract("example.com")
    d = r.data
    assert d["snapshot_count"] == 5
    assert d["first_seen"].startswith("2010")
    assert d["last_seen"].startswith("2024")
    assert sorted(d["years_observed"]) == ["2010", "2013", "2020", "2024"]
    assert ("2013", 2) in d["year_histogram_top"]


def test_commoncrawl_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web

    class _Resp:
        status_code = 200
        text = (
            '{"status":"200","mime":"text/html","url":"https://example.com/"}\n'
            '{"status":"200","mime":"text/html","url":"https://example.com/blog/post-1"}\n'
            '{"status":"404","mime":"text/html","url":"https://example.com/old/missing"}\n'
        )

    class _Client:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url): return _Resp()

    monkeypatch.setattr(web.httpx, "Client", lambda **kw: _Client())
    monkeypatch.delenv("DSI_DISABLE_COMMONCRAWL", raising=False)
    from signal_architecture.signals.extractors.production.web import CommonCrawlExtractor
    r = CommonCrawlExtractor().extract("example.com")
    d = r.data
    assert d["record_count"] == 3
    status_dict = dict(d["status_top"])
    assert status_dict.get("200") == 2
    assert status_dict.get("404") == 1
    assert abs(d["avg_path_depth"] - (0 + 2 + 2) / 3) < 1e-9


def test_tranco_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import TrancoRankExtractor
    sample = {
        "ranks": [
            {"rank": 12000},
            {"rank": 14000},
            {"rank": 11500},
            {"rank": 15000},
        ],
    }
    monkeypatch.setattr(web, "_json_get", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_TRANCO", raising=False)
    r = TrancoRankExtractor().extract("example.com")
    d = r.data
    assert d["current_rank"] == 12000
    assert d["best_rank"] == 11500
    assert d["worst_rank"] == 15000
    assert d["rank_velocity"] == 12000 - 15000


def test_phishtank_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import PhishTankExtractor

    class _Resp:
        status_code = 200
        text = (
            "example.com\n"
            "phish.example.com\n"
            "other.example.com/login\n"
            "unrelated.org\n"
        )
        def raise_for_status(self): pass

    class _Client:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url): return _Resp()

    monkeypatch.setattr(web.httpx, "Client", lambda **kw: _Client())
    monkeypatch.delenv("DSI_DISABLE_PHISHTANK", raising=False)
    r = PhishTankExtractor().extract("example.com")
    d = r.data
    assert d["exact_match_count"] == 1
    assert d["subdomain_match_count"] == 2
    assert d["listed_on_abuse_feed"] is True


def test_cf_radar_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import CloudflareRadarExtractor
    sample = {
        "success": True,
        "result": {
            "summary_0": {
                "DDOS": "52.5",
                "WAF": "33.0",
                "BOTS": "9.0",
                "OTHER": "5.5",
            },
        },
    }
    monkeypatch.setattr(web, "_json_get", lambda url, **kw: sample)
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "dummy")
    monkeypatch.delenv("DSI_DISABLE_CF_RADAR", raising=False)
    r = CloudflareRadarExtractor().extract("example.com")
    d = r.data
    assert d["success"] is True
    assert d["attack_type_count"] == 4
    assert d["attack_type_top"][0] == ("DDOS", 52.5)


def test_google_transparency_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import web
    from signal_architecture.signals.extractors.production.web import GoogleTransparencyExtractor

    class _Resp:
        status_code = 200
        headers = {
            "strict-transport-security":
                "max-age=31536000; includeSubDomains; preload",
            "content-security-policy": "default-src 'self'",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
        }

    class _Client:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url): return _Resp()

    monkeypatch.setattr(web.httpx, "Client", lambda **kw: _Client())
    monkeypatch.delenv("DSI_DISABLE_GOOGLE_TRANSPARENCY", raising=False)
    r = GoogleTransparencyExtractor().extract("example.com")
    d = r.data
    assert d["https_reachable"] is True
    assert d["hsts_max_age"] == 31536000
    assert d["hsts_include_subdomains"] is True
    assert d["hsts_preload"] is True
    assert d["security_header_score"] == 4
