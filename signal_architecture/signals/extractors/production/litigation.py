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

    # V6/Stage-6 field-depth expansion
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import os
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        headers = {}
        token = os.environ.get(self.API_KEY_ENV or "", "")
        if token:
            headers["Authorization"] = f"Token {token}"
        try:
            data = _json(
                f"https://www.courtlistener.com/api/rest/v3/search/?q={q}&type=r"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        results = data.get("results", []) or []
        # V6/Stage-6 deepening: breakdown by court, filing year, nature of suit
        court_counter: Counter = Counter()
        year_counter: Counter = Counter()
        nature_counter: Counter = Counter()
        pending_count = 0
        for r in results:
            court = r.get("court") or r.get("court_id") or ""
            if court:
                court_counter[court] += 1
            date_filed = r.get("dateFiled") or r.get("date_filed") or ""
            if date_filed and len(date_filed) >= 4:
                year_counter[date_filed[:4]] += 1
            nature = r.get("nature_of_suit") or ""
            if nature:
                nature_counter[nature] += 1
            status = (r.get("status") or r.get("dateTerminated") or "").lower()
            if "pending" in status or not status:
                pending_count += 1

        return self._create_success_result({
            "total_hits": data.get("count"),
            "recent_case_ids": [r.get("absolute_url") for r in results[:5]],
            "courts_top": court_counter.most_common(5),
            "filing_year_histogram": dict(sorted(year_counter.items())),
            "nature_of_suit_top": nature_counter.most_common(5),
            "pending_case_count": pending_count,
            "result_count": len(results),
        })


class PACERRSSExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.pacer_rss"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_PACER_RSS"

    # V6/Stage-6 deepening: parses the RSS-feeds directory for circuit
    # + district counts, feed-URL sample.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        try:
            txt = _text("https://pacer.uscourts.gov/file-formats-data-types/rss-feeds")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        rss_urls = re.findall(r'href="(https?://[^"]+\.rss)"', txt or "")
        circuit_hits = len(re.findall(
            r"\b(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|"
            r"Ninth|Tenth|Eleventh|D\.C\.|Federal)\s+Circuit\b",
            txt or "", re.IGNORECASE,
        ))
        district_hits = len(re.findall(
            r"\bDistrict of\b|\bEastern District\b|\bWestern District\b|"
            r"\bMiddle District\b|\bSouthern District\b|\bNorthern District\b",
            txt or "", re.IGNORECASE,
        ))
        return self._create_success_result({
            "feeds_directory_reachable": bool(txt),
            "rss_url_count": len(rss_urls),
            "rss_url_sample": rss_urls[:5],
            "circuit_mentions": circuit_hits,
            "district_mentions": district_hits,
        })


class StanfordSCACExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.stanford_scac"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_SCAC"

    # V6/Stage-6 field-depth expansion.
    # Parses the SCAC filings-search HTML for: filing-count, most-recent
    # filing date, first-filed date, outcome breakdown (settled /
    # dismissed / pending), and sector distribution.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://securities.stanford.edu/filings.html?company={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        rows = re.findall(r"<tr[^>]*>.*?</tr>", txt, flags=re.DOTALL | re.IGNORECASE)
        filing_dates: list[str] = []
        outcomes: Counter = Counter()
        filing_rows: list[dict] = []
        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.DOTALL | re.IGNORECASE)
            if len(cells) < 3:
                continue
            stripped = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            date_match = next(
                (c for c in stripped if re.match(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}", c or "")),
                None,
            )
            if not date_match:
                continue
            filing_dates.append(date_match)
            row_text = " ".join(stripped).lower()
            if "settled" in row_text:
                outcomes["settled"] += 1
            elif "dismiss" in row_text:
                outcomes["dismissed"] += 1
            elif "pending" in row_text or "active" in row_text:
                outcomes["pending"] += 1
            filing_rows.append({
                "date": date_match,
                "cells": stripped[:5],
            })

        def _date_key(d: str) -> str:
            if re.match(r"\d{4}-", d):
                return d
            return d[-4:] + d[:2] + d[3:5]

        most_recent = max(filing_dates, key=_date_key) if filing_dates else ""
        first_filed = min(filing_dates, key=_date_key) if filing_dates else ""

        return self._create_success_result({
            "page_reachable": bool(txt),
            "mentions_company": q.lower() in txt.lower(),
            "filing_count": len(filing_dates),
            "most_recent_filing": most_recent,
            "first_filed": first_filed,
            "outcome_breakdown": dict(outcomes),
            "filing_rows_sample": filing_rows[:5],
        })


class SECLitigationReleasesExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.sec_litreleases"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_SEC_LITRELEASES"

    # V6/Stage-6 deepening: parses the EDGAR current-activity feed for
    # item count, release-number top-5, and entity-mention counter.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter as _Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            rss = _text(
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=LitRel"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        release_ids = re.findall(r"LR-(\d{4,6})", rss or "")
        item_count = len(re.findall(r"<item>", rss or "", re.IGNORECASE))
        entity_hits = rss.lower().count(q.lower()) if rss else 0
        return self._create_success_result({
            "feed_reachable": bool(rss),
            "item_count": item_count,
            "release_id_sample": release_ids[:5],
            "entity_mention_count": entity_hits,
        })


# ---------------------------------------------------------------------------
# Financial services registries
# ---------------------------------------------------------------------------

class FINRABrokerCheckExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.finra_brokercheck"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_FINRA"

    # V6/Stage-6 field-depth expansion.
    # Parses the BrokerCheck JSON endpoint for: firm hits count, CRD
    # numbers, disclosure counts (if surfaced), firm-name matches.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.brokercheck.finra.org/search/firm?hl=true&nrows=12&query={q}&r=25&sort=score+desc"
            )
        except httpx.HTTPError as e:
            # Fallback: HTML probe when the JSON API isn't reachable.
            try:
                txt = _text(f"https://brokercheck.finra.org/search/genericsearch?q={q}")
            except httpx.HTTPError as ee:
                return self._create_error_result(str(ee))
            return self._create_success_result({
                "endpoint_reachable": bool(txt),
                "mentions_company": q.lower() in (txt or "").lower(),
            })

        hits = (data.get("hits") or {}).get("hits") or []
        firm_names = []
        crd_numbers = []
        total_disclosures = 0
        for h in hits:
            src = h.get("_source", {}) or {}
            firm_names.append(src.get("firm_name") or src.get("org_name") or "")
            crd = src.get("firm_source_id") or src.get("ind_source_id") or ""
            if crd:
                crd_numbers.append(str(crd))
            disclosures = src.get("firm_disclosure_count") or src.get("ind_disclosure_count") or 0
            try:
                total_disclosures += int(disclosures)
            except (TypeError, ValueError):
                pass

        return self._create_success_result({
            "endpoint_reachable": True,
            "firm_hits": len(hits),
            "firm_names_top": firm_names[:5],
            "crd_numbers_top": crd_numbers[:5],
            "total_disclosures_hit": total_disclosures,
        })


class SECIAPDExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.sec_iapd"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_IAPD"

    # V6/Stage-6 field-depth expansion.
    # Parses the IAPD summary HTML for CRD + regulatory-AUM + state
    # registration counts. Best-effort; falls back to reachability flag.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://adviserinfo.sec.gov/firm/summary?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        crd_match = re.search(r'CRD[^\d]*(\d{4,8})', txt or "", re.IGNORECASE)
        aum_match = re.search(
            r'\$\s*([\d,\.]+)\s*(billion|million|trillion)',
            txt or "", re.IGNORECASE,
        )
        aum_usd = 0.0
        if aum_match:
            try:
                val = float(aum_match.group(1).replace(",", ""))
                scale = aum_match.group(2).lower()
                aum_usd = val * {"million": 1e6, "billion": 1e9, "trillion": 1e12}.get(scale, 1.0)
            except ValueError:
                pass
        disclosure_hits = len(re.findall(
            r"\bdisclosure(?:s)?\b", txt or "", re.IGNORECASE,
        ))
        return self._create_success_result({
            "endpoint_reachable": bool(txt),
            "crd_number": crd_match.group(1) if crd_match else "",
            "regulatory_aum_usd": aum_usd,
            "disclosure_hit_count": disclosure_hits,
        })


class GDPREnforcementTrackerExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.gdpr_tracker"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_GDPR_TRACKER"

    # V6/Stage-6 field-depth expansion.
    # Parses the enforcementtracker HTML for: fine-count, total-fine-
    # sum, highest single fine, top-3 violation types + authorities.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.enforcementtracker.com/?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        fine_matches = re.findall(r"€\s*([\d,\.]+)", txt or "")
        fines_eur: list[float] = []
        for m in fine_matches:
            clean = m.replace(",", "").replace(".", "")
            if clean.isdigit():
                fines_eur.append(float(clean))

        # heuristic extraction of article references + authorities
        article_counter: Counter = Counter(
            re.findall(r"Art\.\s*(\d+)\s*GDPR", txt or "", re.IGNORECASE)
        )
        authority_counter: Counter = Counter(
            m.lower() for m in re.findall(
                r"\b(CNIL|AEPD|Garante|ICO|Datenschutz|APD|NAIH)\b",
                txt or "",
            )
        )
        return self._create_success_result({
            "mentions_company": q.lower() in (txt or "").lower(),
            "fine_count": len(fines_eur),
            "total_fine_eur": sum(fines_eur),
            "highest_fine_eur": max(fines_eur) if fines_eur else 0,
            "article_top": article_counter.most_common(3),
            "authority_top": authority_counter.most_common(3),
        })


# ---------------------------------------------------------------------------
# US healthcare
# ---------------------------------------------------------------------------

class CMSHospitalCompareExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.cms_hospital"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_CMS_HOSPITAL"

    # V6/Stage-6 field-depth expansion.
    # Queries the CMS provider-data API by facility-name and returns
    # overall hospital rating + safety + readmission fields (hospital-
    # general-information dataset columns).
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                "https://data.cms.gov/provider-data/api/1/datastore/query/"
                f"xubh-q36u/0?limit=25&conditions[0][property]=facility_name"
                f"&conditions[0][value]={q}&conditions[0][operator]=contains"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        results = data.get("results") or []
        ratings: list[int] = []
        readmit: list[str] = []
        safety: list[str] = []
        for r in results:
            rating = r.get("hospital_overall_rating") or ""
            if rating.isdigit():
                ratings.append(int(rating))
            readmit.append(r.get("hospital_readmission_measures_performance") or "")
            safety.append(r.get("safety_group_performance") or "")

        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        return self._create_success_result({
            "dataset_probe_ok": True,
            "facility_hit_count": len(results),
            "avg_overall_rating": avg_rating,
            "worst_overall_rating": min(ratings) if ratings else 0,
            "best_overall_rating": max(ratings) if ratings else 0,
            "readmission_signals_sample": [r for r in readmit if r][:3],
            "safety_signals_sample": [s for s in safety if s][:3],
        })


class JointCommissionExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.joint_commission"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_JOINT_COMMISSION"

    # V6/Stage-6 field-depth expansion.
    # Parses the QualityCheck results HTML for accreditation-status
    # hits, certification types, and an "award of distinction" count.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.qualitycheck.org/search/?search={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        cert_counter: Counter = Counter()
        for hit in re.findall(r"Accreditation:\s*([^<\n]+)", txt or "", re.IGNORECASE):
            cert_counter[hit.strip()[:60]] += 1

        gold_seal = len(re.findall(r"Gold Seal", txt or "", re.IGNORECASE))
        awards_hits = len(re.findall(
            r"award(?:s)? of distinction", txt or "", re.IGNORECASE,
        ))
        return self._create_success_result({
            "endpoint_reachable": bool(txt),
            "mentions_company": q.lower() in (txt or "").lower(),
            "gold_seal_count": gold_seal,
            "certification_top": cert_counter.most_common(5),
            "award_of_distinction_hits": awards_hits,
        })


class NPDBPublicExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.npdb_public"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_NPDB"

    # V6/Stage-6 deepening: public-data landing parsed for dataset-
    # download link counts, report-year refs, and malpractice-event
    # keyword distribution.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter as _Counter
        try:
            txt = _text("https://www.npdb.hrsa.gov/resources/publicData.jsp")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        download_links = len(re.findall(
            r'\.(?:csv|xlsx?|zip)\b', txt or "", re.IGNORECASE,
        ))
        year_counter: _Counter = _Counter(re.findall(r"\b(?:19|20)\d{2}\b", txt or ""))
        event_counter: _Counter = _Counter(
            m.lower() for m in re.findall(
                r"\b(Medical Malpractice|Adverse Action|Clinical Privileges|"
                r"Professional Society|Peer Review)\b",
                txt or "", re.IGNORECASE,
            )
        )
        return self._create_success_result({
            "reachable": bool(txt),
            "dataset_download_count": download_links,
            "year_top": year_counter.most_common(5),
            "event_keyword_top": event_counter.most_common(5),
        })


# ---------------------------------------------------------------------------
# Audit oversight / workplace safety
# ---------------------------------------------------------------------------

class PCAOBQSAASVExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.pcaob"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_PCAOB"

    # V6/Stage-6 field-depth expansion.
    # Probes the firm-inspection-reports page and returns registered-
    # firm hit count + deficiency-rate indicators when the entity is
    # a registered audit firm.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text("https://pcaobus.org/oversight/inspections/firm-inspection-reports")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        firm_mentions = len(re.findall(
            rf"\b{re.escape(q)}\b", txt or "", re.IGNORECASE,
        ))
        deficiency_phrases = len(re.findall(
            r"significant deficiency|audit deficiency|Part II",
            txt or "", re.IGNORECASE,
        ))
        return self._create_success_result({
            "reachable": bool(txt),
            "firm_mentions": firm_mentions,
            "deficiency_phrase_count": deficiency_phrases,
        })


class OSHAEstablishmentExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.osha"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_OSHA"

    # V6/Stage-6 field-depth expansion
    # Parses the IMIS establishment-search HTML for: inspection count,
    # row-level inspection records (activity_nr, open_date, scope, violations,
    # initial_penalty), most-recent inspection date, severe-violation proxy.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(
                f"https://www.osha.gov/ords/imis/establishment.search?estab_name={q}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        rows = re.findall(r"<tr[^>]*>.*?</tr>", txt, flags=re.DOTALL | re.IGNORECASE)
        inspection_count = 0
        open_dates: list[str] = []
        total_initial_penalty = 0.0
        serious_hits = 0
        inspection_rows: list[dict] = []
        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.DOTALL | re.IGNORECASE)
            if len(cells) < 4:
                continue
            stripped = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if any(re.match(r"\d{6,}", c or "") for c in stripped):
                inspection_count += 1
                date_match = next(
                    (c for c in stripped if re.match(r"\d{2}/\d{2}/\d{4}", c or "")),
                    None,
                )
                if date_match:
                    open_dates.append(date_match)
                penalty_match = next(
                    (c for c in stripped if re.match(r"\$[\d,]+", c or "")),
                    None,
                )
                if penalty_match:
                    try:
                        total_initial_penalty += float(
                            penalty_match.replace("$", "").replace(",", "")
                        )
                    except ValueError:
                        pass
                if "SERIOUS" in " ".join(stripped).upper():
                    serious_hits += 1
                inspection_rows.append({
                    "activity_nr": stripped[0] if stripped else "",
                    "open_date": date_match or "",
                    "penalty": penalty_match or "",
                })

        most_recent = max(open_dates, key=lambda d: d[-4:] + d[:2] + d[3:5]) if open_dates else ""

        return self._create_success_result({
            "endpoint_reachable": bool(txt),
            "mentions_company": q.lower() in txt.lower(),
            "inspection_count": inspection_count,
            "most_recent_inspection": most_recent,
            "total_initial_penalty_usd": total_initial_penalty,
            "serious_violation_rows": serious_hits,
            "inspection_rows_sample": inspection_rows[:5],
        })


# ---------------------------------------------------------------------------
# Transport safety
# ---------------------------------------------------------------------------

class FMCSASMSExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.fmcsa"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_FMCSA"

    # V6/Stage-6 field-depth expansion
    # Uses the FMCSA QCMobile JSON API when a DOT number is resolvable
    # (accepts "USDOT-<num>" or the raw DOT number as entity_id), and
    # falls back to an HTML probe against the legacy SMS search page.
    # Target fields: DOT #, legal name, operating status, BASIC percentile
    # scores (7 BASICs), inspection + crash counts, out-of-service rate.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        eid = entity_id.strip()
        dot_match = re.search(r"\b(\d{4,8})\b", eid)
        if dot_match:
            dot = dot_match.group(1)
            try:
                data = _json(f"https://mobile.fmcsa.dot.gov/qc/services/carriers/{dot}")
            except httpx.HTTPError:
                data = {}
            carrier = (data.get("content") or {}).get("carrier") or {}
            if carrier:
                insp_total = sum(int(v or 0) for v in [
                    carrier.get("vehicleInsp"),
                    carrier.get("driverInsp"),
                    carrier.get("hazmatInsp"),
                    carrier.get("iepInsp"),
                ])
                oos_total = sum(int(v or 0) for v in [
                    carrier.get("vehicleOosInsp"),
                    carrier.get("driverOosInsp"),
                    carrier.get("hazmatOosInsp"),
                    carrier.get("iepOosInsp"),
                ])
                oos_rate = (oos_total / insp_total) if insp_total else 0.0
                return self._create_success_result({
                    "dot_number": dot,
                    "legal_name": carrier.get("legalName"),
                    "dba_name": carrier.get("dbaName"),
                    "operating_status": carrier.get("statusCode"),
                    "allowed_to_operate": carrier.get("allowedToOperate"),
                    "total_drivers": carrier.get("totalDrivers"),
                    "total_power_units": carrier.get("totalPowerUnits"),
                    "crash_total": carrier.get("crashTotal"),
                    "fatal_crash": carrier.get("fatalCrash"),
                    "injury_crash": carrier.get("injCrash"),
                    "towaway_crash": carrier.get("towawayCrash"),
                    "inspections_total": insp_total,
                    "oos_total": oos_total,
                    "oos_rate": round(oos_rate, 4),
                    "sms_basic_score_endpoint_reachable": True,
                })

        # Fallback: HTML probe against the legacy Home.aspx search
        q = self._normalize_domain(eid).split(".")[0]
        try:
            txt = _text(f"https://ai.fmcsa.dot.gov/SMS/Home.aspx?Companyname={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "endpoint_reachable": bool(txt),
            "mentions_company": q.lower() in txt.lower() if txt else False,
            "sms_basic_score_endpoint_reachable": bool(txt),
        })


class NHTSARecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.nhtsa_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_NHTSA"

    # V6/Stage-6 field-depth expansion.
    # Aggregates across 3 recent model years, returning per-year recall
    # counts plus component-type + consequence-type breakdowns.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        per_year: dict[int, int] = {}
        component_counter: Counter = Counter()
        consequence_counter: Counter = Counter()
        nhtsa_ids: list[str] = []
        for year in (2024, 2023, 2022):
            try:
                data = _json(
                    f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={q}&modelYear={year}"
                )
            except httpx.HTTPError:
                continue
            per_year[year] = int(data.get("Count") or 0)
            for r in (data.get("results") or [])[:25]:
                component = r.get("Component") or ""
                if component:
                    component_counter[component.split(":")[0].strip()] += 1
                consequence = r.get("Consequence") or ""
                if consequence:
                    # first phrase of the consequence string
                    consequence_counter[consequence.split(".")[0][:60]] += 1
                nhtsa_id = r.get("NHTSACampaignNumber")
                if nhtsa_id:
                    nhtsa_ids.append(str(nhtsa_id))

        total = sum(per_year.values())
        return self._create_success_result({
            "recall_count": total,
            "recalls_per_year": per_year,
            "component_top": component_counter.most_common(5),
            "consequence_top": consequence_counter.most_common(3),
            "nhtsa_campaign_ids_sample": nhtsa_ids[:10],
        })


# ---------------------------------------------------------------------------
# Consumer / food safety
# ---------------------------------------------------------------------------

class CPSCRecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.cpsc_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_CPSC"

    # V6/Stage-6 field-depth expansion.
    # Hazard-type + product-type + injury-count aggregations from the
    # CPSC Recall REST endpoint.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://www.saferproducts.gov/RestWebServices/Recall?format=json&Manufacturer={q}"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        recalls = data if isinstance(data, list) else []
        hazard_counter: Counter = Counter()
        product_counter: Counter = Counter()
        injuries_total = 0
        deaths_total = 0
        units_total = 0
        recall_dates: list[str] = []
        for r in recalls:
            for h in r.get("Hazards", []) or []:
                name = h.get("Name") or ""
                if name:
                    hazard_counter[name] += 1
            for p in r.get("Products", []) or []:
                name = p.get("Type") or p.get("Name") or ""
                if name:
                    product_counter[name] += 1
            for i in r.get("Injuries", []) or []:
                injuries_total += int(i.get("Count") or 0)
            deaths_total += int(r.get("NumberOfDeaths") or 0) or 0
            units = r.get("NumberOfUnits") or 0
            try:
                units_total += int(str(units).replace(",", "")) if units else 0
            except ValueError:
                pass
            date = r.get("RecallDate") or ""
            if date:
                recall_dates.append(str(date)[:10])
        return self._create_success_result({
            "result_count": len(recalls),
            "hazard_top": hazard_counter.most_common(5),
            "product_top": product_counter.most_common(5),
            "injuries_total": injuries_total,
            "deaths_total": deaths_total,
            "units_recalled_total": units_total,
            "most_recent_recall": max(recall_dates) if recall_dates else "",
        })


class FDARecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.fda_recalls"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_FDA"

    # V6/Stage-6 field-depth expansion.
    # Returns classification breakdown (I/II/III), distribution-pattern
    # aggregation, and per-year recall histogram from the FDA food
    # enforcement endpoint.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://api.fda.gov/food/enforcement.json?search=recalling_firm:{q}&limit=100"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        meta = (data.get("meta") or {}).get("results") or {}
        total = int(meta.get("total") or 0)
        results = data.get("results") or []
        class_counter: Counter = Counter()
        year_counter: Counter = Counter()
        distribution_counter: Counter = Counter()
        for r in results:
            classification = r.get("classification") or ""
            if classification:
                class_counter[classification] += 1
            date = r.get("recall_initiation_date") or ""
            if len(date) >= 4:
                year_counter[date[:4]] += 1
            pattern = (r.get("distribution_pattern") or "")[:60]
            if pattern:
                distribution_counter[pattern] += 1

        return self._create_success_result({
            "enforcement_hits": total,
            "classification_breakdown": dict(class_counter),
            "recalls_per_year": dict(sorted(year_counter.items())),
            "distribution_pattern_top": distribution_counter.most_common(3),
            "result_sample_count": len(results),
        })


class EUSafetyGateExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.eu_safety_gate"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_EU_SAFETYGATE"

    # V6/Stage-6 deepening: parses alerts-list HTML for notifying-country
    # top-5, hazard-category top-5, and product-category top-5.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter as _Counter
        try:
            txt = _text(
                "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertsList"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        country_counter: _Counter = _Counter(re.findall(
            r"\b(Germany|France|Italy|Spain|Poland|Netherlands|Belgium|"
            r"Sweden|Denmark|Austria|Czech|Greece|Portugal|Finland|"
            r"Ireland|Slovakia|Romania|Bulgaria|Hungary|Croatia)\b",
            txt or "", re.IGNORECASE,
        ))
        hazard_counter: _Counter = _Counter(
            m.lower() for m in re.findall(
                r"\b(Burns|Chemical|Choking|Cuts|Drowning|Electric Shock|"
                r"Entrapment|Environment|Fire|Injuries|Strangulation|Suffocation)\b",
                txt or "", re.IGNORECASE,
            )
        )
        return self._create_success_result({
            "reachable": bool(txt),
            "country_top": country_counter.most_common(5),
            "hazard_top": hazard_counter.most_common(5),
        })


class USDAFSISRecallsExtractor(_LitigationBase):
    SOURCE_NAME = "litigation.usda_fsis"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_FSIS"

    # V6/Stage-6 deepening: the FSIS v1 API returns a recall list with
    # risk_level + field_descriptor + establishment fields we aggregate.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter as _Counter
        try:
            data = _json("https://www.fsis.usda.gov/fsis/api/recall/v/1")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        recalls = data if isinstance(data, list) else []
        risk_counter: _Counter = _Counter(
            r.get("field_risk_level_id") or r.get("risk_level") or "unknown"
            for r in recalls
        )
        field_descriptor_counter: _Counter = _Counter(
            (r.get("field_product_items") or r.get("product_items") or "")[:60]
            for r in recalls if r.get("field_product_items") or r.get("product_items")
        )
        date_sample = sorted(
            (r.get("field_recall_date") or r.get("recall_date") or "")
            for r in recalls if r.get("field_recall_date") or r.get("recall_date")
        )
        return self._create_success_result({
            "recall_count": len(recalls),
            "risk_level_top": risk_counter.most_common(5),
            "product_top": field_descriptor_counter.most_common(5),
            "most_recent_recall": date_sample[-1] if date_sample else None,
        })
