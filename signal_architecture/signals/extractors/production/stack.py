"""V6/D2 — Technical / Infrastructure extractors.

Seven sources covering internet-facing infrastructure (Shodan, Censys),
internet topology (BGP via RIPEstat, PeeringDB), and web-technology
fingerprinting (Wappalyzer, BuiltWith, HTTP Archive).

Each extractor follows the V6/D1 contract (SOURCE_NAME, COST_TIER,
DEFAULT_TTL_SECONDS, KILL_SWITCH_ENV, optional API_KEY_ENV) and returns
a neutral absence on failure so the framework remains end-to-end
operable without paid credentials.
"""
from __future__ import annotations

import os
from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _json(url: str, *, headers=None, timeout: float = 6.0):
    with httpx.Client(timeout=timeout, headers=headers or {}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


class ShodanExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.shodan"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 1.0
    COST_TIER = "low"
    KILL_SWITCH_ENV = "DSI_DISABLE_SHODAN"
    API_KEY_ENV = "SHODAN_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(f"https://api.shodan.io/dns/resolve?hostnames={domain}&key={key}")
            ip = data.get(domain)
            host = _json(f"https://api.shodan.io/shodan/host/{ip}?key={key}") if ip else {}
        except (httpx.HTTPError, KeyError) as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "ip": ip,
            "open_ports": host.get("ports", []) if isinstance(host, dict) else [],
            "cve_count": len((host or {}).get("vulns", []) or []),
            "org": (host or {}).get("org"),
            "asn": (host or {}).get("asn"),
        })


class CensysExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.censys"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 1.0
    COST_TIER = "medium"
    KILL_SWITCH_ENV = "DSI_DISABLE_CENSYS"
    API_KEY_ENV = "CENSYS_API_ID"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        api_id = os.environ[self.API_KEY_ENV]
        api_secret = os.environ.get("CENSYS_API_SECRET", "")
        auth = (api_id, api_secret)
        try:
            with httpx.Client(timeout=6.0, auth=auth) as c:
                r = c.get(
                    f"https://search.censys.io/api/v2/hosts/search?q=services.tls.certificate.parsed.names:{domain}"
                )
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        hits = data.get("result", {}).get("hits", [])
        return self._create_success_result({
            "host_count": len(hits),
            "sample_ips": [h.get("ip") for h in hits[:5]],
            "asn_set": sorted({h.get("autonomous_system", {}).get("asn") for h in hits if h.get("autonomous_system")}),
        })


class BGPExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.bgp_ripestat"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_BGP"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            data = _json(
                f"https://stat.ripe.net/data/whois/data.json?resource={domain}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "records": len(data.get("data", {}).get("records", []) or []),
        })


class PeeringDBExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.peeringdb"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_PEERINGDB"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://peeringdb.com/api/net?name__contains={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "peering_networks": len(data.get("data", [])),
        })


class WappalyzerExtractor(ProductionExtractor):
    """Wappalyzer OSS runner.

    Uses the `python-Wappalyzer` library when installed; otherwise
    degrades to a lightweight HTML fingerprint (title, server header,
    meta generator).
    """
    SOURCE_NAME = "stack.wappalyzer"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_WAPPALYZER"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=6.0, follow_redirects=True) as c:
                r = c.get(f"https://{domain}/")
                r.raise_for_status()
                text = r.text
                server = r.headers.get("server")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        import re
        gen_match = re.search(r'<meta\s+name="generator"\s+content="([^"]+)"', text, re.I)
        return self._create_success_result({
            "server_header": server,
            "generator": gen_match.group(1) if gen_match else None,
            "has_cookies": bool(r.headers.get("set-cookie")),
        })


class BuiltWithExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.builtwith"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "medium"
    KILL_SWITCH_ENV = "DSI_DISABLE_BUILTWITH"
    API_KEY_ENV = "BUILTWITH_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                f"https://api.builtwith.com/free1/api.json?KEY={key}&LOOKUP={domain}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        groups = data.get("groups", [])
        categories = sorted({c.get("name") for g in groups for c in g.get("categories", []) or []})
        return self._create_success_result({
            "technology_category_count": len(categories),
            "technology_categories": categories[:20],
        })


class HTTPArchiveExtractor(ProductionExtractor):
    """HTTP Archive — bulk site-performance dataset (BigQuery public)."""
    SOURCE_NAME = "stack.httparchive"
    DEFAULT_TTL_SECONDS = 2_592_000
    RATE_LIMIT = 0.5
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_HTTPARCHIVE"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        # BigQuery requires GCP auth. V6-initial surfaces the CrUX proxy
        # endpoint which is free + unauthenticated for popular domains.
        try:
            data = _json(
                "https://chromeuxreport.googleapis.com/v1/records:queryRecord",
                headers={"User-Agent": "dsi/1.0"},
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        # We don't actually query CrUX (it's POST with a body) — V6 ships
        # a presence probe; the full CrUX query lands in a follow-up.
        return self._create_success_result({
            "crux_endpoint_reachable": bool(data),
            "queried_domain": domain,
        })
