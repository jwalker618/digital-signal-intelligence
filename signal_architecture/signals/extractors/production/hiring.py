"""V6/D7 — Hiring / behavioural-derivative extractors.

Four scrapers pull open-job counts from ATS platforms (Greenhouse,
Lever, Ashby) and aggregate search (Google Jobs via SerpAPI-style
fallback). The rolling 90-day delta feeds
``world_engine/derivatives/velocity.py`` which surfaces
``hiring_velocity`` across every affected coverage.

V6/Stage-6 deepened — each extractor now returns structured fields
beyond a plain open-job count.
"""
from __future__ import annotations

import os
from collections import Counter
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

    # V6/Stage-6 deepening: department top-5, office + location top-5,
    # remote-friendly counter, open-job total, plus the sample list.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        dept_counter: Counter = Counter()
        office_counter: Counter = Counter()
        location_counter: Counter = Counter()
        remote_count = 0
        for j in jobs:
            for d in (j.get("departments") or []):
                if d.get("name"):
                    dept_counter[d["name"]] += 1
            for o in (j.get("offices") or []):
                if o.get("name"):
                    office_counter[o["name"]] += 1
            loc = (j.get("location") or {}).get("name") or ""
            if loc:
                location_counter[loc] += 1
                if "remote" in loc.lower():
                    remote_count += 1
        return self._create_success_result({
            "open_jobs": len(jobs),
            "department_top": dept_counter.most_common(5),
            "office_top": office_counter.most_common(5),
            "location_top": location_counter.most_common(5),
            "remote_job_count": remote_count,
            "sample_departments": [d for d, _ in dept_counter.most_common(10)],
        })


class LeverScraper(_HiringBase):
    SOURCE_NAME = "hiring.lever"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_LEVER"

    # V6/Stage-6 deepening: parses Lever postings for team + commitment
    # (full-time/contract) + location distribution + remote count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        postings = data if isinstance(data, list) else []
        team_counter: Counter = Counter()
        commit_counter: Counter = Counter()
        location_counter: Counter = Counter()
        remote_count = 0
        for p in postings:
            cats = p.get("categories") or {}
            team = cats.get("team") or ""
            if team:
                team_counter[team] += 1
            commit = cats.get("commitment") or ""
            if commit:
                commit_counter[commit] += 1
            loc = cats.get("location") or ""
            if loc:
                location_counter[loc] += 1
                if "remote" in loc.lower():
                    remote_count += 1
        return self._create_success_result({
            "open_jobs": len(postings),
            "team_top": team_counter.most_common(5),
            "commitment_top": commit_counter.most_common(5),
            "location_top": location_counter.most_common(5),
            "remote_job_count": remote_count,
        })


class AshbyScraper(_HiringBase):
    SOURCE_NAME = "hiring.ashby"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_ASHBY"

    # V6/Stage-6 deepening: Ashby job-board response exposes
    # department / location / employmentType — all surfaced here.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        slug = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        dept_counter: Counter = Counter()
        location_counter: Counter = Counter()
        emp_type_counter: Counter = Counter()
        remote_count = 0
        for j in jobs:
            d = j.get("department") or ""
            if d:
                dept_counter[d] += 1
            loc = j.get("location") or ""
            if loc:
                location_counter[loc] += 1
                if "remote" in loc.lower():
                    remote_count += 1
            et = j.get("employmentType") or ""
            if et:
                emp_type_counter[et] += 1
        return self._create_success_result({
            "open_jobs": len(jobs),
            "department_top": dept_counter.most_common(5),
            "location_top": location_counter.most_common(5),
            "employment_type_top": emp_type_counter.most_common(5),
            "remote_job_count": remote_count,
        })


class GoogleJobsExtractor(_HiringBase):
    SOURCE_NAME = "hiring.google_jobs"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_GOOGLE_JOBS"
    API_KEY_ENV = "SERPAPI_API_KEY"

    # V6/Stage-6 deepening: SerpAPI google_jobs response parsed for
    # company + employment-type + via-source distributions.
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
        company_counter: Counter = Counter()
        employment_counter: Counter = Counter()
        via_counter: Counter = Counter()
        for j in jobs:
            name = j.get("company_name") or ""
            if name:
                company_counter[name] += 1
            via_counter[j.get("via") or ""] += 1
            ext = (j.get("detected_extensions") or {})
            sched = ext.get("schedule_type") or ""
            if sched:
                employment_counter[sched] += 1
        return self._create_success_result({
            "result_count": len(jobs),
            "company_top": company_counter.most_common(5),
            "employment_top": employment_counter.most_common(5),
            "via_top": via_counter.most_common(5),
        })
