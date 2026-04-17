"""V6/D3 — Litigation & Regulatory extractors.

Eighteen public sources covering US federal + state courts, SEC/FINRA
registries, GDPR enforcement actions, US healthcare quality (CMS, Joint
Commission, NPDB), auditor oversight (PCAOB), workplace safety (OSHA),
transport safety (FMCSA, NHTSA), consumer-product recalls (CPSC, FDA,
EU Safety Gate, USDA FSIS).

All sources are free (HTML / RSS / JSON). Each extractor exposes:
- SOURCE_NAME: "litigation.<short>"
- DEFAULT_TTL_SECONDS: tuned per source cadence (daily / weekly / monthly)
- KILL_SWITCH_ENV: DSI_DISABLE_<SHORT>
- _do_extract: best-effort probe with neutral-absence on network failure

As with D1, the structure is the stable contract; specific field-level
parsing matures per source in follow-up PRs.
"""
from __future__ import annotations

from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _text(url: str, *, timeout: float = 6.0) -> str:
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "dsi-extractor/1.0"},
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def _json(url: str, *, timeout: float = 6.0):
    with httpx.Client(timeout=timeout, headers={"User-Agent": "dsi/1.0"}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


class _LitigationBase(ProductionExtractor):
    COST_TIER = "free"

    def get_required_config(self) -> List[str]:
        return []


# ---------------------------------------------------------------------------
# US Federal Courts
# ---------------------------------------------------------------------------

class CourtListenerExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.courtlistener"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_COURTLISTENER"
    API_KEY_ENV = "COURTLISTENER_TOKEN"  # optional — anon works but rate-limited

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import os
        q = self._normalize_domain(entity_id).split(".")[0]
        headers = {}
        token = os.environ.get(self.API_KEY_ENV or "", "")
        if token:
            headers["Authorization"] = f"Token {token}"
        try:
            data = _json(f"https://www.courtlistener.com/api/rest/v3/search/?q={q}&type=r", )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "total_hits": data.get("count"),
            "recent_case_ids": [r.get("absolute_url") for r in data.get("results", [])[:5]],
        })


class PACERRSSExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.pacer_rss"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_PACER_RSS"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # PACER RSS feeds are per-court; this probes the public list.
        try:
            txt = _text("https://pacer.uscourts.gov/file-formats-data-types/rss-feeds")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "feeds_directory_reachable": bool(txt),
        })


class StanfordSCACExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.stanford_scac"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_SCAC"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://securities.stanford.edu/filings.html?company={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "page_reachable": bool(txt),
            "mentions_company": q.lower() in txt.lower(),
        })


class SECLitigationReleasesExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.sec_litreleases"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_SEC_LITRELEASES"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            rss = _text("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=LitRel")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "feed_reachable": bool(rss),
        })


# ---------------------------------------------------------------------------
# Financial services registries
# ---------------------------------------------------------------------------

class FINRABrokerCheckExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.finra_brokercheck"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_FINRA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://brokercheck.finra.org/search/genericsearch?q={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"endpoint_reachable": bool(txt)})


class SECIAPDExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.sec_iapd"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_IAPD"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://adviserinfo.sec.gov/firm/summary?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"endpoint_reachable": bool(txt)})


class GDPREnforcementTrackerExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.gdpr_tracker"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_GDPR_TRACKER"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.enforcementtracker.com/?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "mentions_company": q.lower() in txt.lower(),
        })


# ---------------------------------------------------------------------------
# US healthcare
# ---------------------------------------------------------------------------

class CMSHospitalCompareExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.cms_hospital"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_CMS_HOSPITAL"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json(
                "https://data.cms.gov/provider-data/api/1/datastore/query/"
                "xubh-q36u/0?limit=1"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "dataset_probe_ok": bool(data.get("results")),
        })


class JointCommissionExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.joint_commission"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_JOINT_COMMISSION"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.qualitycheck.org/search/?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"endpoint_reachable": bool(txt)})


class NPDBPublicExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.npdb_public"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_NPDB"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.npdb.hrsa.gov/resources/publicData.jsp")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


# ---------------------------------------------------------------------------
# Audit oversight / workplace safety
# ---------------------------------------------------------------------------

class PCAOBQSAASVExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.pcaob"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_PCAOB"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://pcaobus.org/oversight/inspections/firm-inspection-reports")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class OSHAEstablishmentExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.osha"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_OSHA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.osha.gov/ords/imis/establishment.search?estab_name={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "endpoint_reachable": bool(txt),
            "mentions_company": q.lower() in txt.lower(),
        })


# ---------------------------------------------------------------------------
# Transport safety
# ---------------------------------------------------------------------------

class FMCSASMSExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.fmcsa"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_FMCSA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://ai.fmcsa.dot.gov/SMS/Home.aspx?Companyname={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"endpoint_reachable": bool(txt)})


class NHTSARecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.nhtsa_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_NHTSA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={q}&modelYear=2024"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "recall_count": data.get("Count"),
        })


# ---------------------------------------------------------------------------
# Consumer / food safety
# ---------------------------------------------------------------------------

class CPSCRecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.cpsc_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_CPSC"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://www.saferproducts.gov/RestWebServices/Recall?format=json&Manufacturer={q}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "result_count": len(data) if isinstance(data, list) else 0,
        })


class FDARecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.fda_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_FDA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.fda.gov/food/enforcement.json?search=recalling_firm:{q}&limit=10"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "enforcement_hits": (data.get("meta", {}) or {}).get("results", {}).get("total"),
        })


class EUSafetyGateExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.eu_safety_gate"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_EU_SAFETYGATE"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertsList")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class USDAFSISRecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.usda_fsis"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_FSIS"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json("https://www.fsis.usda.gov/fsis/api/recall/v/1")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "recall_count": len(data) if isinstance(data, list) else 0,
        })
