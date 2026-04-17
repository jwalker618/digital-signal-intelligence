"""V6/D2 — technical/infrastructure extractor smoke tests."""
from __future__ import annotations

import importlib

import pytest


EXPECTED_D2 = {
    "stack.shodan",
    "stack.censys",
    "stack.bgp_ripestat",
    "stack.peeringdb",
    "stack.wappalyzer",
    "stack.builtwith",
    "stack.httparchive",
}


@pytest.fixture()
def factory_module():
    from signal_architecture.signals.extractors.production import factory
    importlib.reload(factory)
    return factory


def test_all_d2_extractors_registered(factory_module):
    reg = factory_module._registry.list_extractors()
    missing = EXPECTED_D2 - set(reg)
    assert not missing, f"missing D2 extractors: {sorted(missing)}"


def test_shodan_kill_switch(monkeypatch):
    from signal_architecture.signals.extractors.production.stack import ShodanExtractor
    monkeypatch.setenv("DSI_DISABLE_SHODAN", "true")
    result = ShodanExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "kill_switch_active"


def test_builtwith_requires_api_key(monkeypatch):
    from signal_architecture.signals.extractors.production.stack import BuiltWithExtractor
    monkeypatch.delenv("BUILTWITH_API_KEY", raising=False)
    monkeypatch.delenv("DSI_DISABLE_BUILTWITH", raising=False)
    result = BuiltWithExtractor().extract("example.com")
    assert result.metadata["absence_reason"] == "api_key_missing"


def test_wappalyzer_is_free_and_no_api_key():
    from signal_architecture.signals.extractors.production.stack import WappalyzerExtractor
    assert WappalyzerExtractor.COST_TIER == "free"
    assert WappalyzerExtractor.API_KEY_ENV is None


def test_cost_tier_ordering():
    from signal_architecture.signals.extractors.production.stack import (
        BGPExtractor, ShodanExtractor, CensysExtractor,
    )
    # free < low < medium
    assert BGPExtractor.cost_tier_rank() < ShodanExtractor.cost_tier_rank()
    assert ShodanExtractor.cost_tier_rank() < CensysExtractor.cost_tier_rank()


# V6/Stage-6 deepened-parsing tests — D2 stack extractors.


def test_shodan_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import ShodanExtractor
    call_count = {"n": 0}

    def fake_json(url, **kw):
        call_count["n"] += 1
        if "dns/resolve" in url:
            return {"example.com": "1.2.3.4"}
        return {
            "ip": "1.2.3.4",
            "ports": [80, 443, 22],
            "vulns": ["CVE-2024-1234", "CVE-2024-5678"],
            "org": "ACME ISP",
            "asn": "AS65000",
            "country_code": "US",
            "city": "San Francisco",
            "os": "Linux",
            "data": [
                {"product": "nginx", "_shodan": {"module": "http"}},
                {"product": "nginx", "_shodan": {"module": "https"}},
                {"product": "OpenSSH", "_shodan": {"module": "ssh"}},
            ],
        }

    monkeypatch.setattr(stack, "_json", fake_json)
    monkeypatch.setenv("SHODAN_API_KEY", "dummy")
    monkeypatch.delenv("DSI_DISABLE_SHODAN", raising=False)
    r = ShodanExtractor().extract("example.com")
    d = r.data
    assert d["ip"] == "1.2.3.4"
    assert d["open_ports"] == [80, 443, 22]
    assert d["cve_count"] == 2
    assert ("nginx", 2) in d["product_top"]
    assert d["country_code"] == "US"


def test_bgp_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import BGPExtractor
    sample = {
        "data": {
            "records": [
                [
                    {"key": "inetnum", "value": "1.2.3.0 - 1.2.3.255"},
                    {"key": "mnt-by", "value": "EXAMPLE-MNT"},
                    {"key": "source", "value": "RIPE"},
                    {"key": "origin", "value": "AS65000"},
                ],
            ],
        },
    }
    monkeypatch.setattr(stack, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_BGP", raising=False)
    r = BGPExtractor().extract("example.com")
    d = r.data
    assert d["record_count"] == 1
    auth_names = [a for a, _ in d["authority_top"]]
    assert "EXAMPLE-MNT" in auth_names
    assert "AS65000" in d["origin_asn_sample"]


def test_peeringdb_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import PeeringDBExtractor
    sample = {
        "data": [
            {"asn": 65000, "info_traffic": "100-200Gbps", "policy_general": "Open"},
            {"asn": 65001, "info_traffic": "100-200Gbps", "policy_general": "Selective"},
            {"asn": 65002, "info_traffic": "200-500Gbps", "policy_general": "Open"},
        ],
    }
    monkeypatch.setattr(stack, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_PEERINGDB", raising=False)
    r = PeeringDBExtractor().extract("example.com")
    d = r.data
    assert d["peering_networks"] == 3
    assert 65000 in d["asn_sample"]
    assert ("100-200Gbps", 2) in d["info_traffic_top"]
    assert ("Open", 2) in d["policy_general_top"]


def test_wappalyzer_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import WappalyzerExtractor

    html_body = (
        '<html><head>'
        '<title>Example — Home</title>'
        '<link rel="canonical" href="https://example.com/">'
        '<meta name="generator" content="WordPress 6.3">'
        '<script src="https://cdn.example.com/app.js"></script>'
        '<script src="https://cdn.example.com/vendor.js"></script>'
        '<script src="https://cdn.jsdelivr.net/react.js"></script>'
        '</head><body>'
        '<div id="__NEXT_DATA__"></div>'
        '/wp-content/themes/example/style.css'
        '</body></html>'
    )

    class _Resp:
        status_code = 200
        headers = {"server": "nginx/1.25", "set-cookie": "x=1"}
        text = html_body
        def raise_for_status(self): pass

    class _Client:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url): return _Resp()

    monkeypatch.setattr(stack.httpx, "Client", lambda **kw: _Client())
    monkeypatch.delenv("DSI_DISABLE_WAPPALYZER", raising=False)

    r = WappalyzerExtractor().extract("example.com")
    d = r.data
    assert d["server_header"] == "nginx/1.25"
    assert d["generator"] == "WordPress 6.3"
    assert d["title"] == "Example — Home"
    assert "wordpress" in d["frameworks_detected"]
    assert "nextjs" in d["frameworks_detected"]
    assert ("cdn.example.com", 2) in d["script_host_top"]


def test_builtwith_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import BuiltWithExtractor
    sample = {
        "groups": [
            {
                "categories": [{"name": "Analytics"}, {"name": "CDN"}],
                "technologies": [
                    {"name": "Google Analytics", "lastDetected": "20240901"},
                    {"name": "Cloudflare", "lastDetected": "20241215"},
                ],
            },
            {
                "categories": [{"name": "Framework"}],
                "technologies": [
                    {"name": "React", "lastDetected": "20241201"},
                ],
            },
        ],
    }
    monkeypatch.setattr(stack, "_json", lambda url, **kw: sample)
    monkeypatch.setenv("BUILTWITH_API_KEY", "dummy")
    monkeypatch.delenv("DSI_DISABLE_BUILTWITH", raising=False)
    r = BuiltWithExtractor().extract("example.com")
    d = r.data
    assert d["technology_category_count"] == 3
    assert "Google Analytics" in d["technology_names_sample"]
    assert d["last_detected_max"] == "20241215"


def test_httparchive_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import stack
    from signal_architecture.signals.extractors.production.stack import HTTPArchiveExtractor

    class _Resp:
        status_code = 200
        def json(self):
            return {
                "record": {
                    "key": {"origin": "https://example.com", "formFactor": "PHONE"},
                    "metrics": {
                        "largest_contentful_paint": {"percentiles": {"p75": 2400}},
                        "cumulative_layout_shift": {"percentiles": {"p75": 0.08}},
                        "interaction_to_next_paint": {"percentiles": {"p75": 150}},
                        "first_contentful_paint": {"percentiles": {"p75": 1200}},
                    },
                    "collectionPeriod": {"firstDate": "2024-11-01", "lastDate": "2024-11-28"},
                },
            }

    class _Client:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def post(self, url, **kw): return _Resp()

    monkeypatch.setattr(stack.httpx, "Client", lambda **kw: _Client())
    monkeypatch.delenv("DSI_DISABLE_HTTPARCHIVE", raising=False)

    r = HTTPArchiveExtractor().extract("example.com")
    d = r.data
    assert d["lcp_p75_ms"] == 2400
    assert d["cls_p75"] == 0.08
    assert d["inp_p75_ms"] == 150
    assert d["form_factor"] == "PHONE"
    assert d["crux_endpoint_reachable"] is True
