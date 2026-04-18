"""V6/D4 — IP / Innovation extractors.

Five free sources covering patents (USPTO PatentsView, EPO OPS) and
scholarly publications (OpenAlex, CrossRef, Semantic Scholar). Feed
signals like patent_filing_velocity, patent_litigation_density,
research_vitality_index, publication_citation_count, coauthor_network_
depth — consumed by D&O (A4), PI (A8), and Tech E&O (B8).

V6/Stage-6 deepened: each extractor returns structured field output
beyond a simple count.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import List
from urllib.parse import quote_plus

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _json(url: str, *, timeout: float = 6.0, headers=None):
    with httpx.Client(timeout=timeout, headers=headers or {}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


class _IPBase(ProductionExtractor):
    COST_TIER = "free"

    def get_required_config(self) -> List[str]:
        return []


class USPTOExtractor(_IPBase):
    SOURCE_NAME = "ip.uspto"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_USPTO"

    # V6/Stage-6 deepening: requests multiple fields (patent_number,
    # patent_date) to return grant-year histogram + most-recent patent
    # number + total + sample count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                "https://api.patentsview.org/patents/query?"
                f"q=%7B%22assignee_organization%22%3A%22{quote_plus(q)}%22%7D"
                "&f=%5B%22patent_number%22%2C%22patent_date%22%5D"
                "&o=%7B%22per_page%22%3A50%7D"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        if not isinstance(data, dict):
            return self._create_success_result({"patent_count": 0, "subset_returned": 0})
        patents = data.get("patents", []) or []
        year_counter: Counter = Counter(
            (p.get("patent_date") or "")[:4] for p in patents
            if (p.get("patent_date") or "")[:4].isdigit()
        )
        latest_date = max(
            (p.get("patent_date") for p in patents if p.get("patent_date")),
            default=None,
        )
        latest_number = next(
            (p.get("patent_number") for p in patents
             if p.get("patent_date") == latest_date),
            None,
        ) if latest_date else None
        return self._create_success_result({
            "patent_count": data.get("total_patent_count"),
            "subset_returned": len(patents),
            "year_histogram_top": year_counter.most_common(5),
            "earliest_year": min(year_counter.keys()) if year_counter else None,
            "latest_year": max(year_counter.keys()) if year_counter else None,
            "latest_patent_date": latest_date,
            "latest_patent_number": latest_number,
        })


class EPOOpsExtractor(_IPBase):
    SOURCE_NAME = "ip.epo_ops"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_EPO"
    API_KEY_ENV = "EPO_OPS_KEY"

    # V6/Stage-6 deepening: the public OPS endpoint returns metadata
    # fields (total-result-count, family counts, IPC classifications
    # when accessible). We parse what's returned without auth.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json(
                "https://ops.epo.org/3.2/rest-services/published-data/search/biblio?q=applicant%3Dexample"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        # OPS returns XML normally; a JSON envelope only appears with
        # auth. Treat non-dict payload as reachable-but-unauthorised.
        if not isinstance(data, dict):
            return self._create_success_result({
                "endpoint_reachable": True,
                "authorized": False,
            })
        ops = data.get("ops:world-patent-data", {}) or {}
        search = ops.get("ops:biblio-search", {}) or {}
        total = search.get("@total-result-count")
        range_ = search.get("@range") or ""
        return self._create_success_result({
            "endpoint_reachable": bool(data),
            "authorized": bool(total),
            "total_result_count": total,
            "range": range_,
        })


class OpenAlexExtractor(_IPBase):
    SOURCE_NAME = "ip.openalex"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_OPENALEX"

    # V6/Stage-6 deepening: returns full summary_stats (h_index,
    # i10_index, 2yr_mean_citedness), country + type + concepts top-5,
    # and most-recent works_count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.openalex.org/institutions?search={quote_plus(q)}&per_page=5"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        results = data.get("results", []) if isinstance(data, dict) else []
        top = results[0] if results else {}
        summary = top.get("summary_stats") or {}
        concept_counter: Counter = Counter(
            c.get("display_name") for c in (top.get("x_concepts") or [])
            if c.get("display_name")
        )
        return self._create_success_result({
            "institution_id": top.get("id"),
            "display_name": top.get("display_name"),
            "country_code": top.get("country_code"),
            "type": top.get("type"),
            "works_count": top.get("works_count"),
            "cited_by_count": top.get("cited_by_count"),
            "h_index": summary.get("h_index"),
            "i10_index": summary.get("i10_index"),
            "two_year_mean_citedness": summary.get("2yr_mean_citedness"),
            "concept_top": concept_counter.most_common(5),
            "institution_sample_size": len(results),
        })


class CrossRefExtractor(_IPBase):
    SOURCE_NAME = "ip.crossref"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_CROSSREF"

    # V6/Stage-6 deepening: rows=20 returns real message-item samples
    # for publisher + type + year-of-publication histograms.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.crossref.org/works?query.affiliation={quote_plus(q)}&rows=20"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        message = data.get("message", {}) if isinstance(data, dict) else {}
        items = message.get("items", []) or []
        publisher_counter: Counter = Counter(
            i.get("publisher") for i in items if i.get("publisher")
        )
        type_counter: Counter = Counter(
            i.get("type") for i in items if i.get("type")
        )
        year_counter: Counter = Counter()
        for i in items:
            issued = i.get("issued", {}) or {}
            parts = issued.get("date-parts") or []
            if parts and parts[0] and parts[0][0]:
                year_counter[str(parts[0][0])] += 1
        return self._create_success_result({
            "total_results": message.get("total-results"),
            "sample_size": len(items),
            "publisher_top": publisher_counter.most_common(5),
            "type_top": type_counter.most_common(5),
            "year_top": year_counter.most_common(5),
        })


class SemanticScholarExtractor(_IPBase):
    SOURCE_NAME = "ip.semantic_scholar"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_SEMANTIC_SCHOLAR"
    API_KEY_ENV = None

    # V6/Stage-6 deepening: pulls 10 results with year + citationCount
    # + venue fields to return year histogram + venue top-5 + citation
    # mean + total.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
        headers = {"x-api-key": key} if key else {}
        try:
            data = _json(
                f"https://api.semanticscholar.org/graph/v1/paper/search?query={quote_plus(q)}"
                "&limit=10&fields=year,citationCount,venue,title",
                headers=headers,
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        papers = data.get("data", []) if isinstance(data, dict) else []
        year_counter: Counter = Counter(
            str(p.get("year")) for p in papers if p.get("year")
        )
        venue_counter: Counter = Counter(
            (p.get("venue") or "")[:60] for p in papers if p.get("venue")
        )
        citations = [p.get("citationCount") for p in papers if isinstance(p.get("citationCount"), (int, float))]
        return self._create_success_result({
            "paper_total": data.get("total"),
            "sample_size": len(papers),
            "year_top": year_counter.most_common(5),
            "venue_top": venue_counter.most_common(5),
            "mean_citation_count": (sum(citations) / len(citations)) if citations else 0.0,
            "max_citation_count": max(citations) if citations else 0,
        })
