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
        return self._create_success_result({
            "public_repos": data.get("public_repos"),
            "followers": data.get("followers"),
            "created_at": data.get("created_at"),
            "verified_email_domain": data.get("email") or None,
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
        domain = self._normalize_domain(entity_id)
        url = (
            "https://web.archive.org/cdx/search/cdx?"
            f"url={domain}&output=json&limit=1&fl=timestamp,original&from=1996"
        )
        try:
            data = _json_get(url)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        rows = data[1:] if isinstance(data, list) and len(data) > 1 else []
        first_ts = rows[0][0] if rows else None
        return self._create_success_result({
            "first_seen": first_ts,
            "snapshot_available": bool(rows),
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
        # CC-MAIN-YYYY-WW index — we hit the latest index summary only.
        domain = self._normalize_domain(entity_id)
        index = kwargs.get("cc_index", "CC-MAIN-2025-13")
        url = f"https://index.commoncrawl.org/{index}-index?url=*.{domain}&output=json&limit=1"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
            present = resp.status_code == 200 and bool(resp.text.strip())
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "present_in_index": present,
            "index": index,
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
        domain = self._normalize_domain(entity_id)
        url = f"https://tranco-list.eu/api/ranks/domain/{domain}"
        try:
            data = _json_get(url)
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        ranks = data.get("ranks", [])
        latest = ranks[0].get("rank") if ranks else None
        return self._create_success_result({
            "current_rank": latest,
            "history_points": len(ranks),
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
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(self.FEED_URL)
                resp.raise_for_status()
                text = resp.text.lower()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        present = domain.lower() in text
        return self._create_success_result({
            "listed_on_abuse_feed": present,
            "feed": self.SOURCE_NAME,
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
        return self._create_success_result({
            "raw_summary": data.get("result", {}),
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
        # HTTPS-posture scraping is JSONP-based and brittle; we ship a
        # working probe but downstream signal is limited to boolean
        # "responds on https" for V6 initial. Follow-up phase deepens this.
        domain = self._normalize_domain(entity_id)
        try:
            with httpx.Client(timeout=5.0, follow_redirects=False) as client:
                resp = client.get(f"https://{domain}/")
        except httpx.HTTPError:
            return self._create_success_result({"https_reachable": False})
        return self._create_success_result({
            "https_reachable": resp.status_code < 400,
            "status_code": resp.status_code,
            "hsts_header": resp.headers.get("strict-transport-security"),
        })
