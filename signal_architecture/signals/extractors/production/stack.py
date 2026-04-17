"""V6/D2 — Technical / Infrastructure extractors.

Seven sources covering internet-facing infrastructure (Shodan, Censys),
internet topology (BGP via RIPEstat, PeeringDB), and web-technology
fingerprinting (Wappalyzer, BuiltWith, HTTP Archive).

Each extractor follows the V6/D1 contract (SOURCE_NAME, COST_TIER,
DEFAULT_TTL_SECONDS, KILL_SWITCH_ENV, optional API_KEY_ENV) and returns
a neutral absence on failure so the framework remains end-to-end
operable without paid credentials.

V6/Stage-6 deepened: each extractor returns structured field output
beyond a reachability flag.
"""
from __future__ import annotations

import os
import re
from collections import Counter
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

    # V6/Stage-6 deepening: returns per-port service + product fingerprints
    # from the Shodan host record, plus CVE sample and country/city.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(f"https://api.shodan.io/dns/resolve?hostnames={domain}&key={key}")
            ip = data.get(domain)
            host = _json(f"https://api.shodan.io/shodan/host/{ip}?key={key}") if ip else {}
        except (httpx.HTTPError, KeyError) as e:
            return self._create_error_result(str(e))
        services = host.get("data", []) if isinstance(host, dict) else []
        product_counter: Counter = Counter(
            s.get("product") for s in services if s.get("product")
        )
        service_counter: Counter = Counter(
            s.get("_shodan", {}).get("module") for s in services
            if s.get("_shodan", {}).get("module")
        )
        cves = (host or {}).get("vulns", []) or []
        return self._create_success_result({
            "ip": ip,
            "open_ports": host.get("ports", []) if isinstance(host, dict) else [],
            "cve_count": len(cves),
            "cve_sample": sorted(cves)[:10],
            "org": (host or {}).get("org"),
            "asn": (host or {}).get("asn"),
            "country_code": (host or {}).get("country_code"),
            "city": (host or {}).get("city"),
            "os": (host or {}).get("os"),
            "product_top": product_counter.most_common(5),
            "service_module_top": service_counter.most_common(5),
            "service_count": len(services),
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

    # V6/Stage-6 deepening: ASN + service top-5 + location hint from
    # the Censys hits page.
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
        hits = data.get("result", {}).get("hits", []) or []
        service_counter: Counter = Counter()
        country_counter: Counter = Counter()
        for h in hits:
            for s in h.get("services", []) or []:
                svc = s.get("service_name") or ""
                if svc:
                    service_counter[svc] += 1
            loc = h.get("location", {}) or {}
            country = loc.get("country_code") or ""
            if country:
                country_counter[country] += 1
        return self._create_success_result({
            "host_count": len(hits),
            "sample_ips": [h.get("ip") for h in hits[:5]],
            "asn_set": sorted({
                h.get("autonomous_system", {}).get("asn")
                for h in hits if h.get("autonomous_system")
            }),
            "service_top": service_counter.most_common(5),
            "country_top": country_counter.most_common(5),
        })


class BGPExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.bgp_ripestat"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_BGP"

    def get_required_config(self) -> List[str]:
        return []

    # V6/Stage-6 deepening: whois records + inetnum / origin-ASN +
    # authority heuristics from RIPEstat whois view.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            data = _json(
                f"https://stat.ripe.net/data/whois/data.json?resource={domain}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        records = (data.get("data", {}) or {}).get("records", []) or []
        flat = [kv for rec in records for kv in (rec or [])]
        auth_counter: Counter = Counter(
            kv.get("value") for kv in flat
            if kv.get("key") in {"mnt-by", "mnt-ref", "source", "org", "authority"}
            and kv.get("value")
        )
        inetnums = [kv.get("value") for kv in flat if kv.get("key") == "inetnum" and kv.get("value")]
        origin_asns = [kv.get("value") for kv in flat if kv.get("key") == "origin" and kv.get("value")]
        return self._create_success_result({
            "record_count": len(records),
            "unique_key_count": len({kv.get("key") for kv in flat if kv.get("key")}),
            "authority_top": auth_counter.most_common(5),
            "inetnum_sample": inetnums[:3],
            "origin_asn_sample": origin_asns[:3],
        })


class PeeringDBExtractor(ProductionExtractor):
    SOURCE_NAME = "stack.peeringdb"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_PEERINGDB"

    def get_required_config(self) -> List[str]:
        return []

    # V6/Stage-6 deepening: net records deserialised for ASN,
    # info_traffic-band distribution, and policy-general distribution.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://peeringdb.com/api/net?name__contains={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        rows = data.get("data", []) or []
        asns = [r.get("asn") for r in rows if r.get("asn")]
        traffic_counter: Counter = Counter(
            r.get("info_traffic") for r in rows if r.get("info_traffic")
        )
        policy_counter: Counter = Counter(
            r.get("policy_general") for r in rows if r.get("policy_general")
        )
        return self._create_success_result({
            "peering_networks": len(rows),
            "asn_sample": asns[:10],
            "info_traffic_top": traffic_counter.most_common(5),
            "policy_general_top": policy_counter.most_common(5),
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

    # V6/Stage-6 deepening: richer HTML fingerprint (title, canonical,
    # framework-signature detection, script-src host top-5).
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

        gen_match = re.search(
            r'<meta\s+name="generator"\s+content="([^"]+)"', text, re.I,
        )
        title_match = re.search(r"<title>([^<]{1,200})</title>", text, re.I)
        canonical_match = re.search(
            r'<link\s+rel="canonical"\s+href="([^"]+)"', text, re.I,
        )
        frameworks = []
        for fw, pat in (
            ("react", r"\b__REACT_DEVTOOLS_GLOBAL_HOOK__\b|react\.production\b|_reactRootContainer\b"),
            ("vue", r"\bVue\.config\b|data-v-[a-f0-9]{8}"),
            ("angular", r"ng-version=|@angular/core"),
            ("wordpress", r"/wp-content/|wp-includes"),
            ("drupal", r"Drupal\.settings|drupal-"),
            ("django", r"csrfmiddlewaretoken"),
            ("nextjs", r"__NEXT_DATA__"),
        ):
            if re.search(pat, text, re.I):
                frameworks.append(fw)

        script_hosts: Counter = Counter(
            m.group(1)
            for m in re.finditer(r'<script[^>]+src="https?://([^/"]+)', text, re.I)
        )

        return self._create_success_result({
            "server_header": server,
            "generator": gen_match.group(1) if gen_match else None,
            "title": title_match.group(1).strip() if title_match else None,
            "canonical": canonical_match.group(1) if canonical_match else None,
            "frameworks_detected": frameworks,
            "script_host_top": script_hosts.most_common(5),
            "has_cookies": bool(r.headers.get("set-cookie")),
            "page_size_bytes": len(text.encode("utf-8", errors="ignore")),
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

    # V6/Stage-6 deepening: category + tech-name breakdown + last-seen
    # date window from the BuiltWith free1 endpoint.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                f"https://api.builtwith.com/free1/api.json?KEY={key}&LOOKUP={domain}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        groups = data.get("groups", []) or []
        categories = set()
        tech_names = set()
        last_detected = []
        for g in groups:
            for c in g.get("categories", []) or []:
                name = c.get("name")
                if name:
                    categories.add(name)
            for t in g.get("technologies", []) or []:
                tech = t.get("name")
                if tech:
                    tech_names.add(tech)
                ld = t.get("lastDetected")
                if ld:
                    last_detected.append(ld)
        return self._create_success_result({
            "technology_category_count": len(categories),
            "technology_categories": sorted(categories)[:20],
            "technology_name_count": len(tech_names),
            "technology_names_sample": sorted(tech_names)[:20],
            "last_detected_max": max(last_detected) if last_detected else None,
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

    # V6/Stage-6 deepening: queries the CrUX-report endpoint with a
    # domain body, parsing LCP + CLS + INP + navigation form-factor
    # fields when available.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.post(
                    "https://chromeuxreport.googleapis.com/v1/records:queryRecord",
                    json={"origin": f"https://{domain}"},
                    headers={"User-Agent": "dsi/1.0"},
                )
                if resp.status_code >= 400:
                    data = {}
                else:
                    data = resp.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        record = (data.get("record") or {}) if isinstance(data, dict) else {}
        metrics = record.get("metrics", {}) or {}
        def _p75(metric_key: str):
            m = metrics.get(metric_key, {}) or {}
            p = m.get("percentiles", {}) or {}
            return p.get("p75")
        return self._create_success_result({
            "crux_endpoint_reachable": bool(record),
            "queried_domain": domain,
            "lcp_p75_ms": _p75("largest_contentful_paint"),
            "cls_p75": _p75("cumulative_layout_shift"),
            "inp_p75_ms": _p75("interaction_to_next_paint"),
            "fcp_p75_ms": _p75("first_contentful_paint"),
            "collection_period": record.get("collectionPeriod"),
            "form_factor": (record.get("key", {}) or {}).get("formFactor"),
        })
