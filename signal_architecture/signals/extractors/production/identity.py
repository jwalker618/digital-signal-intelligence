"""V6/D1 — Identity / breach exposure extractors."""
from __future__ import annotations

import os
from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


class HIBPExtractor(ProductionExtractor):
    SOURCE_NAME = "identity.hibp"
    DEFAULT_TTL_SECONDS = 604_800  # weekly
    RATE_LIMIT = 2.0
    COST_TIER = "low"
    KILL_SWITCH_ENV = "DSI_DISABLE_HIBP"
    API_KEY_ENV = "HIBP_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        headers = {"hibp-api-key": key, "User-Agent": "dsi-extractor/1.0"}
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    f"https://haveibeenpwned.com/api/v3/breaches?domain={domain}",
                    headers=headers,
                )
                resp.raise_for_status()
                breaches = resp.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "breach_count": len(breaches),
            "breach_names": [b.get("Name") for b in breaches],
            "latest_breach_date": max(
                (b.get("BreachDate") for b in breaches if b.get("BreachDate")),
                default=None,
            ),
        })


class IntelXExtractor(ProductionExtractor):
    SOURCE_NAME = "identity.intelx"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 1.0
    COST_TIER = "medium"
    KILL_SWITCH_ENV = "DSI_DISABLE_INTELX"
    API_KEY_ENV = "INTELX_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Minimal V6 probe: search IntelX for domain-keyed leaks.
        # The IntelX API requires a POST with a search term then polling
        # by id; for V6 initial we issue the search and surface the
        # queued-id + estimated result count. Full ingestion lands with D8.
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        headers = {"x-key": key}
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    "https://free.intelx.io/intelligent/search",
                    headers=headers,
                    json={"term": domain, "maxresults": 10, "media": 0, "sort": 4},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "search_id": data.get("id"),
            "estimated_results": data.get("count"),
        })
