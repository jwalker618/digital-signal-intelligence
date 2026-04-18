"""V6/D1 — Universal Web Footprint extractors.

Ten free / freemium sources covering a company's externally observable
web presence (SCM, archive, infra, rank, abuse feeds, transparency).

Each extractor declares the V6 D1 contract (SOURCE_NAME, COST_TIER,
DEFAULT_TTL_SECONDS, KILL_SWITCH_ENV, optional API_KEY_ENV) and
implements ``_do_extract``. The initial implementations return a neutral
absence when the upstream is unreachable / unauthorized so the framework
runs end-to-end without credentials; real HTTP calls are filled in per
extractor as integrations are validated in staging.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


# ---------------------------------------------------------------------------
# Common helper — minimal JSON GET with a short timeout. Any failure is
# funnelled through _create_error_result which downgrades to absence-as-signal
# at the resolver layer.
# ---------------------------------------------------------------------------

def _json_get(url: str, *, headers: Optional[Dict[str, str]] = None, timeout: float = 5.0) -> Any:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers=headers or {})
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# GitHub organisation footprint
# ---------------------------------------------------------------------------

class GitHubOrgExtractor(ProductionExtractor):
    SOURCE_NAME = "web.github_org"
    DEFAULT_TTL_SECONDS = 86_400  # daily
    RATE_LIMIT = 5.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_GITHUB_ORG"
    API_KEY_ENV = "GITHUB_PAT"  # optional — unauth also works but lower rate

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        org = self._normalize_domain(entity_id).split(".")[0]
        import os
        headers = {}
        token = os.environ.get(self.API_KEY_ENV or "", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            data = _json_get(f"https://api.github.com/orgs/{org}", headers=headers)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        # V6/Stage-6 deepening: return richer org profile + infer
        # activity-era band from created_at.
        created = data.get("created_at") or ""
        try:
            year = int(created[:4]) if created else 0
        except ValueError:
            year = 0
        era = (
            "2020s" if year >= 2020 else
            "2010s" if year >= 2010 else
            "2000s" if year >= 2000 else
            "unknown"
        )
        return self._create_success_result({
            "public_repos": data.get("public_repos"),
            "public_gists": data.get("public_gists"),
            "followers": data.get("followers"),
            "following": data.get("following"),
            "created_at": created,
            "updated_at": data.get("updated_at"),
            "era_band": era,
            "verified_email_domain": data.get("email") or None,
            "blog": data.get("blog"),
            "location": data.get("location"),
            "company": data.get("company"),
            "is_verified": bool(data.get("is_verified")),
        })


# ---------------------------------------------------------------------------
# Wayback Machine (Internet Archive) — first-seen date + snapshot count
# ---------------------------------------------------------------------------

class WaybackExtractor(ProductionExtractor):
    SOURCE_NAME = "web.wayback"
    DEFAULT_TTL_SECONDS = 604_800  # weekly
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_WAYBACK"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: aggregate CDX snapshots across full
        # history to return first-seen, last-seen, total count, and a
        # per-year histogram.
        domain = self._normalize_domain(entity_id)
        url = (
            "https://web.archive.org/cdx/search/cdx?"
            f"url={domain}&output=json&limit=500&fl=timestamp&from=1996"
        )
        try:
            data = _json_get(url)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        rows = data[1:] if isinstance(data, list) and len(data) > 1 else []
        timestamps = [r[0] for r in rows if r and r[0]]
        from collections import Counter as _Counter
        year_histogram = _Counter(ts[:4] for ts in timestamps if len(ts) >= 4)
        first_ts = min(timestamps) if timestamps else None
        last_ts = max(timestamps) if timestamps else None
        return self._create_success_result({
            "first_seen": first_ts,
            "last_seen": last_ts,
            "snapshot_available": bool(rows),
            "snapshot_count": len(rows),
            "years_observed": sorted(year_histogram.keys()),
            "year_histogram_top": year_histogram.most_common(5),
        })


# ---------------------------------------------------------------------------
# urlscan.io — free tier 500/day, infrastructure linkages
# ---------------------------------------------------------------------------

class URLScanExtractor(ProductionExtractor):
    SOURCE_NAME = "web.urlscan"
    DEFAULT_TTL_SECONDS = 3_600  # hourly
    RATE_LIMIT = 2.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_URLSCAN"
    API_KEY_ENV = "URLSCAN_API_KEY"  # optional; anon also works (rate-limited)

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import os
        domain = self._normalize_domain(entity_id)
        headers = {}
        key = os.environ.get(self.API_KEY_ENV or "", "")
        if key:
            headers["API-Key"] = key
        try:
            data = _json_get(
                f"https://urlscan.io/api/v1/search/?q=domain:{domain}",
                headers=headers,
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        results = data.get("results", [])
        return self._create_success_result({
            "scan_count": len(results),
            "recent_ips": list({r.get("page", {}).get("ip") for r in results if r.get("page")}),
            "recent_asns": list({r.get("page", {}).get("asn") for r in results if r.get("page")}),
        })


# ---------------------------------------------------------------------------
# Common Crawl — bulk crawl presence
# ---------------------------------------------------------------------------

class CommonCrawlExtractor(ProductionExtractor):
    SOURCE_NAME = "web.commoncrawl"
    DEFAULT_TTL_SECONDS = 2_592_000  # monthly
    RATE_LIMIT = 1.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_COMMONCRAWL"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: parses the line-delimited JSON from
        # Common Crawl for status-code + mime-type + URL-path-depth
        # distributions in addition to the presence flag.
        domain = self._normalize_domain(entity_id)
        index = kwargs.get("cc_index", "CC-MAIN-2025-13")
        url = (
            f"https://index.commoncrawl.org/{index}-index?url=*.{domain}"
            "&output=json&limit=50"
        )
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                text = resp.text
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        from collections import Counter as _Counter
        import json as _json
        records = []
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(_json.loads(line))
            except ValueError:
                continue
        status_counter: _Counter = _Counter(
            str(r.get("status", "")) for r in records if r.get("status")
        )
        mime_counter: _Counter = _Counter(
            str(r.get("mime", ""))[:30] for r in records if r.get("mime")
        )
        path_depths = []
        for r in records:
            u = r.get("url") or ""
            if "://" in u:
                path = u.split("://", 1)[1].split("/", 1)
                depth = len(path[1].strip("/").split("/")) if len(path) > 1 and path[1] else 0
                path_depths.append(depth)
        avg_path_depth = (sum(path_depths) / len(path_depths)) if path_depths else 0.0
        return self._create_success_result({
            "present_in_index": bool(records),
            "index": index,
            "record_count": len(records),
            "status_top": status_counter.most_common(3),
            "mime_top": mime_counter.most_common(3),
            "avg_path_depth": avg_path_depth,
        })


# ---------------------------------------------------------------------------
# Tranco — stable domain rank
# ---------------------------------------------------------------------------

class TrancoRankExtractor(ProductionExtractor):
    SOURCE_NAME = "web.tranco"
    DEFAULT_TTL_SECONDS = 86_400  # daily
    RATE_LIMIT = 2.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_TRANCO"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: besides the latest rank, return min /
        # max / mean rank, rank-velocity (latest minus oldest), and a
        # best-month vs worst-month marker.
        domain = self._normalize_domain(entity_id)
        url = f"https://tranco-list.eu/api/ranks/domain/{domain}"
        try:
            data = _json_get(url)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        ranks = data.get("ranks", []) or []
        rank_vals = [
            r.get("rank") for r in ranks
            if isinstance(r.get("rank"), (int, float))
        ]
        latest = rank_vals[0] if rank_vals else None
        first = rank_vals[-1] if rank_vals else None
        return self._create_success_result({
            "current_rank": latest,
            "history_points": len(ranks),
            "best_rank": min(rank_vals) if rank_vals else None,
            "worst_rank": max(rank_vals) if rank_vals else None,
            "mean_rank": (sum(rank_vals) / len(rank_vals)) if rank_vals else None,
            "rank_velocity": (latest - first) if (latest is not None and first is not None) else None,
        })


# ---------------------------------------------------------------------------
# Google Safe Browsing — malware + phishing flags
# ---------------------------------------------------------------------------

class GoogleSafeBrowsingExtractor(ProductionExtractor):
    SOURCE_NAME = "web.safebrowsing"
    DEFAULT_TTL_SECONDS = 86_400  # daily
    RATE_LIMIT = 2.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_SAFEBROWSING"
    API_KEY_ENV = "GOOGLE_SAFEBROWSING_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import os
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]  # guaranteed by has_api_key() gate
        url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"
        payload = {
            "client": {"clientId": "dsi", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": f"https://{domain}/"}],
            },
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        matches = data.get("matches", [])
        return self._create_success_result({
            "flagged": bool(matches),
            "threat_types": sorted({m.get("threatType") for m in matches}),
        })


# ---------------------------------------------------------------------------
# PhishTank + OpenPhish — simple "is this domain on the abuse list?"
# ---------------------------------------------------------------------------

class _AbuseFeedExtractor(ProductionExtractor):
    FEED_URL: str = ""

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: reports the exact-match line count +
        # neighbourhood hits (subdomain / path-prefix matches) alongside
        # the binary presence flag so downstream callers can rank
        # severity.
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(self.FEED_URL)
                resp.raise_for_status()
                text = resp.text.lower()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        lines = text.splitlines()
        exact_hits = sum(1 for ln in lines if domain.lower() == ln.strip().lower())
        subdomain_hits = sum(
            1 for ln in lines
            if domain.lower() in ln.lower() and ln.strip().lower() != domain.lower()
        )
        root = domain.split(".")[0]
        root_hits = sum(1 for ln in lines if root.lower() in ln.lower())
        return self._create_success_result({
            "listed_on_abuse_feed": exact_hits > 0 or subdomain_hits > 0,
            "feed": self.SOURCE_NAME,
            "exact_match_count": exact_hits,
            "subdomain_match_count": subdomain_hits,
            "root_token_match_count": root_hits,
            "feed_line_count": len(lines),
        })


class PhishTankExtractor(_AbuseFeedExtractor):
    SOURCE_NAME = "web.phishtank"
    DEFAULT_TTL_SECONDS = 86_400
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_PHISHTANK"
    FEED_URL = "https://data.phishtank.com/data/online-valid.csv"


class OpenPhishExtractor(_AbuseFeedExtractor):
    SOURCE_NAME = "web.openphish"
    DEFAULT_TTL_SECONDS = 86_400
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_OPENPHISH"
    FEED_URL = "https://openphish.com/feed.txt"


# ---------------------------------------------------------------------------
# Cloudflare Radar + Google Transparency — aggregate attack / HTTPS posture
# ---------------------------------------------------------------------------

class CloudflareRadarExtractor(ProductionExtractor):
    SOURCE_NAME = "web.cloudflare_radar"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 2.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_CF_RADAR"
    API_KEY_ENV = "CLOUDFLARE_API_TOKEN"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: projects the Cloudflare Radar summary
        # into top attack-type + human-bot ratio + success fields.
        import os
        domain = self._normalize_domain(entity_id)
        url = (
            "https://api.cloudflare.com/client/v4/radar/attacks/layer7/summary"
            f"?dateRange=7d&name={domain}"
        )
        headers = {"Authorization": f"Bearer {os.environ[self.API_KEY_ENV]}"}
        try:
            data = _json_get(url, headers=headers)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        result = data.get("result", {}) or {}
        summary_0 = (result.get("summary_0") or {})
        # Cloudflare returns percentage strings; coerce to float.
        def _pct(v):
            try:
                return float(str(v).rstrip("%"))
            except (TypeError, ValueError):
                return 0.0
        attack_types = [(k, _pct(v)) for k, v in summary_0.items()]
        attack_types.sort(key=lambda t: t[1], reverse=True)
        return self._create_success_result({
            "raw_summary": result,
            "success": bool(data.get("success")),
            "attack_type_top": attack_types[:5],
            "attack_type_count": len(attack_types),
        })


class GoogleTransparencyExtractor(ProductionExtractor):
    SOURCE_NAME = "web.google_transparency"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 2.0
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_GOOGLE_TRANSPARENCY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # V6/Stage-6 deepening: parses HSTS max-age + includeSubDomains
        # + preload flags, detects HTTP→HTTPS upgrade, and captures a
        # set of common security headers' presence.
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=5.0, follow_redirects=False) as client:
                resp = client.get(f"https://{domain}/")
        except httpx.HTTPError:
            return self._create_success_result({"https_reachable": False})

        hsts = resp.headers.get("strict-transport-security", "") or ""
        hsts_max_age = 0
        if "max-age=" in hsts.lower():
            try:
                hsts_max_age = int(
                    hsts.lower().split("max-age=", 1)[1].split(";", 1)[0].strip()
                )
            except (ValueError, IndexError):
                pass
        hsts_include_sub = "includesubdomains" in hsts.lower()
        hsts_preload = "preload" in hsts.lower()

        sec_headers = {
            "content-security-policy": bool(resp.headers.get("content-security-policy")),
            "x-frame-options": bool(resp.headers.get("x-frame-options")),
            "x-content-type-options": bool(resp.headers.get("x-content-type-options")),
            "referrer-policy": bool(resp.headers.get("referrer-policy")),
            "permissions-policy": bool(resp.headers.get("permissions-policy")),
        }
        sec_header_score = sum(1 for v in sec_headers.values() if v)

        return self._create_success_result({
            "https_reachable": resp.status_code < 400,
            "status_code": resp.status_code,
            "hsts_header": hsts or None,
            "hsts_max_age": hsts_max_age,
            "hsts_include_subdomains": hsts_include_sub,
            "hsts_preload": hsts_preload,
            "security_headers_present": sec_headers,
            "security_header_score": sec_header_score,
        })
