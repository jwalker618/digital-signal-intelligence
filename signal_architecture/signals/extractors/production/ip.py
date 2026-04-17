"""V6/D4 — IP / Innovation extractors.

Five free sources covering patents (USPTO PatentsView, EPO OPS) and
scholarly publications (OpenAlex, CrossRef, Semantic Scholar). Feed
signals like patent_filing_velocity, patent_litigation_density,
research_vitality_index, publication_citation_count, coauthor_network_
depth — consumed by D&O (A4), PI (A8), and Tech E&O (B8).
"""
from __future__ import annotations

import os
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
    DEFAULT_TTL_SECONDS = 2_592_000  # monthly
    KILL_SWITCH_ENV = "DSI_DISABLE_USPTO"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                "https://api.patentsview.org/patents/query?"
                f"q=%7B%22assignee_organization%22%3A%22{quote_plus(q)}%22%7D"
                "&f=%5B%22patent_number%22%5D"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "patent_count": data.get("total_patent_count") if isinstance(data, dict) else 0,
            "subset_returned": len(data.get("patents", []) or []) if isinstance(data, dict) else 0,
        })


class EPOOpsExtractor(_IPBase):
    SOURCE_NAME = "ip.epo_ops"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_EPO"
    API_KEY_ENV = "EPO_OPS_KEY"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # EPO OPS is OAuth2; V6 ships reachability-only probe.
        try:
            data = _json(
                "https://ops.epo.org/3.2/rest-services/published-data/search/biblio?q=applicant%3Dexample"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"endpoint_reachable": bool(data)})


class OpenAlexExtractor(_IPBase):
    SOURCE_NAME = "ip.openalex"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_OPENALEX"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.openalex.org/institutions?search={quote_plus(q)}&per_page=1"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        results = data.get("results", []) if isinstance(data, dict) else []
        top = results[0] if results else {}
        return self._create_success_result({
            "institution_id": top.get("id"),
            "works_count": top.get("works_count"),
            "cited_by_count": top.get("cited_by_count"),
            "h_index": (top.get("summary_stats") or {}).get("h_index"),
        })


class CrossRefExtractor(_IPBase):
    SOURCE_NAME = "ip.crossref"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_CROSSREF"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.crossref.org/works?query.affiliation={quote_plus(q)}&rows=1"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        message = data.get("message", {}) if isinstance(data, dict) else {}
        return self._create_success_result({
            "total_results": message.get("total-results"),
        })


class SemanticScholarExtractor(_IPBase):
    SOURCE_NAME = "ip.semantic_scholar"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_SEMANTIC_SCHOLAR"
    API_KEY_ENV = None  # anon works; key boosts rate

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
        headers = {"x-api-key": key} if key else {}
        try:
            data = _json(
                f"https://api.semanticscholar.org/graph/v1/paper/search?query={quote_plus(q)}&limit=1",
                headers=headers,
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "paper_total": data.get("total"),
        })
