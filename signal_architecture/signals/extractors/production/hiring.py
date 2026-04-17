"""V6/D7 — Hiring / behavioural-derivative extractors.

Four scrapers pull open-job counts from ATS platforms (Greenhouse,
Lever, Ashby) and aggregate search (Google Jobs via SerpAPI-style
fallback). The rolling 90-day delta feeds
``world_engine/derivatives/velocity.py`` which surfaces
``hiring_velocity`` across every affected coverage.
"""
from __future__ import annotations

import os
from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _json(url: str, *, timeout: float = 6.0, headers=None):
    with httpx.Client(timeout=timeout, headers=headers or {}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


class _HiringBase(ProductionExtractor):
    COST_TIER = "free"

    def get_required_config(self) -> List[str]:
        return []


class GreenhouseScraper(_HiringBase):
    SOURCE_NAME = "hiring.greenhouse"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_GREENHOUSE"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Greenhouse public-board URL: boards.greenhouse.io/<slug>.json
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        return self._create_success_result({
            "open_jobs": len(jobs),
            "sample_departments": sorted({
                (j.get("departments") or [{}])[0].get("name")
                for j in jobs[:50]
                if j.get("departments")
            })[:10],
        })


class LeverScraper(_HiringBase):
    SOURCE_NAME = "hiring.lever"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_LEVER"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "open_jobs": len(data) if isinstance(data, list) else 0,
        })


class AshbyScraper(_HiringBase):
    SOURCE_NAME = "hiring.ashby"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_ASHBY"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        return self._create_success_result({
            "open_jobs": len(jobs),
        })


class GoogleJobsExtractor(_HiringBase):
    SOURCE_NAME = "hiring.google_jobs"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_GOOGLE_JOBS"
    API_KEY_ENV = "SERPAPI_API_KEY"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                f"https://serpapi.com/search.json?engine=google_jobs&q={q}+jobs&api_key={key}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        jobs = data.get("jobs_results", []) if isinstance(data, dict) else []
        return self._create_success_result({
            "result_count": len(jobs),
        })
