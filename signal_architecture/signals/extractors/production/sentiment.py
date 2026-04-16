"""V6/D1 — Sentiment / public-opinion extractors.

Trustpilot, BBB, Glassdoor, Google Reviews. The first three are
rate-limited scrapers; Google Reviews uses the Places API (paid low).
All implement the neutral-absence contract so the framework still
decisions in their absence.
"""
from __future__ import annotations

import os
from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _fetch_html(url: str, *, timeout: float = 6.0) -> str:
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "dsi-extractor/1.0 (+https://dsi.internal)"},
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


class TrustpilotScraper(ProductionExtractor):
    SOURCE_NAME = "sentiment.trustpilot"
    DEFAULT_TTL_SECONDS = 86_400
    RATE_LIMIT = 0.5
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_TRUSTPILOT"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            html = _fetch_html(f"https://www.trustpilot.com/review/{domain}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        # Lightweight extraction — look for known rating anchors.
        import re
        rating = None
        count = None
        m = re.search(r'"ratingValue"\s*:\s*"?([0-9.]+)', html)
        if m:
            try:
                rating = float(m.group(1))
            except ValueError:
                rating = None
        m = re.search(r'"reviewCount"\s*:\s*"?([0-9]+)', html)
        if m:
            count = int(m.group(1))
        return self._create_success_result({
            "rating": rating,
            "review_count": count,
        })


class BBBScraper(ProductionExtractor):
    SOURCE_NAME = "sentiment.bbb"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 0.5
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_BBB"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            html = _fetch_html(f"https://www.bbb.org/us/search?find_text={domain}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        # V6 initial: presence-only signal (listed / not listed).
        listed = domain in html.lower()
        return self._create_success_result({
            "listed_on_bbb": listed,
        })


class GlassdoorScraper(ProductionExtractor):
    SOURCE_NAME = "sentiment.glassdoor"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 0.5
    COST_TIER = "free"
    KILL_SWITCH_ENV = "DSI_DISABLE_GLASSDOOR"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        try:
            html = _fetch_html(
                f"https://www.glassdoor.com/Search/results.htm?keyword={domain}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "listed_on_glassdoor": domain in html.lower(),
        })


class GoogleReviewsExtractor(ProductionExtractor):
    SOURCE_NAME = "sentiment.google_reviews"
    DEFAULT_TTL_SECONDS = 604_800
    RATE_LIMIT = 2.0
    COST_TIER = "low"
    KILL_SWITCH_ENV = "DSI_DISABLE_GOOGLE_REVIEWS"
    API_KEY_ENV = "GOOGLE_PLACES_API_KEY"

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        domain = self._normalize_domain(entity_id)
        key = os.environ[self.API_KEY_ENV]
        url = (
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            f"?input={domain}&inputtype=textquery&fields=rating,user_ratings_total"
            f"&key={key}"
        )
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        candidates = data.get("candidates", [])
        first = candidates[0] if candidates else {}
        return self._create_success_result({
            "rating": first.get("rating"),
            "review_count": first.get("user_ratings_total"),
            "found": bool(candidates),
        })
