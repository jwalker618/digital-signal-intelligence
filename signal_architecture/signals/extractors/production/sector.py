"""V6/D6 — Sector telemetry extractors.

Aviation (OpenSky, ICAO registry, ASIAS), maritime deep-dive (AIS Hub,
Marine Cadastre, EMSA THETIS, Paris + Tokyo MoU), and energy-asset
telemetry (PHMSA, BSEE detail, NERC violations).

Consumed by Aerospace (A6), Marine (A7), Energy (A8),
Environmental Liability (B4).

V6/Stage-6 deepened — each extractor parses its real response surface
(HTML tables, JSON feeds) and emits structured fields beyond the
reachability flag.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from typing import List

import httpx

from ...types import ExtractorResult
from .base import ProductionExtractor


def _text(url: str, *, timeout: float = 6.0):
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "dsi/1.0"},
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def _json(url: str, *, timeout: float = 6.0, headers=None):
    with httpx.Client(timeout=timeout, headers=headers or {}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


class _SectorBase(ProductionExtractor):
    COST_TIER = "free"

    def get_required_config(self) -> List[str]:
        return []


# ---------------------------------------------------------------------------
# Aviation
# ---------------------------------------------------------------------------

class OpenSkyExtractor(_SectorBase):
    SOURCE_NAME = "sector.opensky"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_OPENSKY"
    API_KEY_ENV = None  # anon works for bounded queries

    # Stage-6 deepening: returns state-vector count, unique-country
    # distribution, and on-ground vs airborne split.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json("https://opensky-network.org/api/states/all?time=0")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        states = data.get("states") if isinstance(data, dict) else None
        states = states or []
        country_counter: Counter = Counter()
        on_ground = 0
        airborne = 0
        for s in states:
            # OpenSky state vector indices: [2]=origin_country, [8]=on_ground
            country = s[2] if len(s) > 2 else ""
            if country:
                country_counter[country.strip()] += 1
            if len(s) > 8 and s[8]:
                on_ground += 1
            else:
                airborne += 1
        return self._create_success_result({
            "states_returned": len(states),
            "country_top": country_counter.most_common(5),
            "on_ground_count": on_ground,
            "airborne_count": airborne,
            "time_snapshot": data.get("time") if isinstance(data, dict) else None,
        })


class ICAORegistryExtractor(_SectorBase):
    SOURCE_NAME = "sector.icao_registry"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ICAO"

    # Stage-6 deepening: counts of published documents + version refs on
    # the ICAO registry landing page.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.icao.int/publications/Pages/doc7300.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        edition_hits = len(re.findall(r"\bEdition\b", txt or "", re.IGNORECASE))
        pdf_links = len(re.findall(r'\.pdf\b', txt or "", re.IGNORECASE))
        annex_hits = len(re.findall(r"\bAnnex\s*\d+\b", txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "edition_hits": edition_hits,
            "pdf_link_count": pdf_links,
            "annex_mention_count": annex_hits,
        })


class ASIASExtractor(_SectorBase):
    SOURCE_NAME = "sector.asias"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ASIAS"

    # Stage-6 deepening: parses ASIAS landing page for section headings,
    # dataset names, and visible-feature count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.asias.faa.gov/apex/f?p=100:1:0::NO:::")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        section_hits = len(re.findall(
            r"<h[12][^>]*>", txt or "", re.IGNORECASE,
        ))
        dataset_mentions = len(re.findall(
            r"\b(ACAS|NASDAC|AIDS|Safety Study|Accident|Incident)\b",
            txt or "", re.IGNORECASE,
        ))
        link_count = len(re.findall(r'<a\s+href="', txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "heading_count": section_hits,
            "dataset_keyword_hits": dataset_mentions,
            "internal_link_count": link_count,
        })


# ---------------------------------------------------------------------------
# Maritime deep-dive
# ---------------------------------------------------------------------------

class AISHubExtractor(_SectorBase):
    SOURCE_NAME = "sector.ais_hub"
    DEFAULT_TTL_SECONDS = 3_600
    KILL_SWITCH_ENV = "DSI_DISABLE_AIS_HUB"
    API_KEY_ENV = "AIS_HUB_API_KEY"
    COST_TIER = "low"

    # Stage-6 deepening: parses AIS Hub rows for flag/country distribution,
    # ship-type breakdown, and speed-over-ground summary.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                f"https://data.aishub.net/ws.php?username={key}&format=1&output=json"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        rows = data[1] if isinstance(data, list) and len(data) > 1 else []
        flag_counter: Counter = Counter()
        ship_type_counter: Counter = Counter()
        speeds: list[float] = []
        for r in rows[:500]:
            flag = r.get("FLAG") or r.get("flag") or ""
            if flag:
                flag_counter[str(flag)] += 1
            st = r.get("TYPE") or r.get("ship_type") or ""
            if st:
                ship_type_counter[str(st)] += 1
            sog = r.get("SOG")
            if sog is None:
                sog = r.get("speed_over_ground")
            try:
                if sog is not None:
                    speeds.append(float(sog))
            except (TypeError, ValueError):
                pass
        return self._create_success_result({
            "ship_rows_probe": len(rows),
            "flag_top": flag_counter.most_common(5),
            "ship_type_top": ship_type_counter.most_common(5),
            "avg_speed_over_ground": (sum(speeds) / len(speeds)) if speeds else 0.0,
            "speed_sample_size": len(speeds),
        })


class MarineCadastreExtractor(_SectorBase):
    SOURCE_NAME = "sector.marine_cadastre"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_MARINE_CADASTRE"

    # Stage-6 deepening: parses the AIS landing page for hyperlink count,
    # dataset-download keywords, and update-year references.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://marinecadastre.gov/ais/")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        dl_hits = len(re.findall(r"\bdownload\b", txt or "", re.IGNORECASE))
        year_hits = Counter(re.findall(r"\b20\d{2}\b", txt or ""))
        zone_hits = len(re.findall(
            r"\b(UTM\s*Zone|EEZ|territorial)\b", txt or "", re.IGNORECASE,
        ))
        return self._create_success_result({
            "reachable": bool(txt),
            "download_keyword_count": dl_hits,
            "year_top": year_hits.most_common(5),
            "zone_keyword_count": zone_hits,
        })


class EMSAExtractor(_SectorBase):
    SOURCE_NAME = "sector.emsa_thetis"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_EMSA"

    # Stage-6 deepening: parses THETIS-MRV portal for CO2 / emission
    # keywords, report-year references, and link counts.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://portal.emsa.europa.eu/web/thetis-mrv")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        co2_hits = len(re.findall(r"CO2|CO\u2082", txt or "", re.IGNORECASE))
        mrv_hits = len(re.findall(r"\bMRV\b", txt or ""))
        year_counter = Counter(re.findall(r"\b20\d{2}\b", txt or ""))
        return self._create_success_result({
            "reachable": bool(txt),
            "co2_mention_count": co2_hits,
            "mrv_mention_count": mrv_hits,
            "year_top": year_counter.most_common(5),
        })


class ParisMoUExtractor(_SectorBase):
    SOURCE_NAME = "sector.paris_mou"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_PARIS_MOU"

    # Stage-6 deepening: inspection-search page parsed for form fields,
    # performance-list links, and detention-related keywords.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://parismou.org/inspection-search")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        detention_hits = len(re.findall(r"\bdetention", txt or "", re.IGNORECASE))
        perf_list_hits = len(re.findall(
            r"\b(?:black|grey|white)\s+list\b", txt or "", re.IGNORECASE,
        ))
        form_inputs = len(re.findall(r'<input\b', txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "detention_mention_count": detention_hits,
            "performance_list_hits": perf_list_hits,
            "search_form_input_count": form_inputs,
        })


class TokyoMoUExtractor(_SectorBase):
    SOURCE_NAME = "sector.tokyo_mou"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_TOKYO_MOU"

    # Stage-6 deepening: PSC database landing parsed for inspection /
    # detention / flag keyword counts.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.tokyo-mou.org/inspections_detentions/psc_database.php")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        detention_hits = len(re.findall(r"detention", txt or "", re.IGNORECASE))
        inspection_hits = len(re.findall(r"inspection", txt or "", re.IGNORECASE))
        flag_hits = len(re.findall(r"flag state|Flag State", txt or ""))
        return self._create_success_result({
            "reachable": bool(txt),
            "detention_mention_count": detention_hits,
            "inspection_mention_count": inspection_hits,
            "flag_state_mention_count": flag_hits,
        })


# ---------------------------------------------------------------------------
# Energy assets
# ---------------------------------------------------------------------------

class PHMSAExtractor(_SectorBase):
    SOURCE_NAME = "sector.phmsa"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_PHMSA"

    # Stage-6 deepening: incident-statistics landing parsed for
    # reporting-year refs, hazmat / gas / liquid split keywords, and
    # CSV / XLS dataset link counts.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text(
                "https://www.phmsa.dot.gov/data-and-statistics/pipeline/incident-statistics"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        year_counter = Counter(re.findall(r"\b20\d{2}\b", txt or ""))
        hazmat_hits = len(re.findall(r"\bhazmat\b", txt or "", re.IGNORECASE))
        gas_hits = len(re.findall(r"\bnatural\s*gas\b", txt or "", re.IGNORECASE))
        liquid_hits = len(re.findall(
            r"hazardous\s*liquid", txt or "", re.IGNORECASE,
        ))
        dataset_links = len(re.findall(r"\.(?:csv|xlsx?)\b", txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "year_top": year_counter.most_common(5),
            "hazmat_mention_count": hazmat_hits,
            "gas_mention_count": gas_hits,
            "liquid_mention_count": liquid_hits,
            "dataset_link_count": dataset_links,
        })


class BSEEDetailExtractor(_SectorBase):
    SOURCE_NAME = "sector.bsee_detail"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_BSEE"

    # Stage-6 deepening: Incidents.aspx parsed for severity keywords,
    # year refs, operator-name mention count, and report link count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.data.bsee.gov/Main/Incidents.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        severity_counter: Counter = Counter(
            m.upper() for m in re.findall(
                r"\b(INJURY|FATALITY|FIRE|EXPLOSION|SPILL)\b", txt or "",
                re.IGNORECASE,
            )
        )
        year_counter = Counter(re.findall(r"\b20\d{2}\b", txt or ""))
        link_count = len(re.findall(r'<a\s+href="', txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "severity_top": severity_counter.most_common(5),
            "year_top": year_counter.most_common(5),
            "link_count": link_count,
        })


class NERCVioExtractor(_SectorBase):
    SOURCE_NAME = "sector.nerc_violations"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_NERC"

    # Stage-6 deepening: compliance-enforcement landing page parsed for
    # standard references (CIP, BAL, TOP, etc.) and penalty-amount
    # hints.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.nerc.com/pa/comp/ce/Pages/default.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        standard_counter: Counter = Counter(
            re.findall(r"\b(CIP|BAL|TOP|VAR|COM|FAC|PRC|EOP|IRO)-\d{3}\b",
                       txt or "")
        )
        penalty_matches = re.findall(r"\$\s*([\d,\.]+)", txt or "")
        penalty_usd = 0.0
        for m in penalty_matches:
            try:
                penalty_usd += float(m.replace(",", ""))
            except ValueError:
                pass
        return self._create_success_result({
            "reachable": bool(txt),
            "standard_top": standard_counter.most_common(5),
            "penalty_sum_usd": penalty_usd,
            "penalty_ref_count": len(penalty_matches),
        })
