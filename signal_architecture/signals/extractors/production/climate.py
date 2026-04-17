"""V6/D5 — Climate / Environment extractors.

Eleven free public datasets covering natural-hazard exposure (FEMA flood,
NOAA storms, USFS wildfire, USGS seismic, NHC hurricane), satellite
imagery (Copernicus), climate reanalysis (ECMWF ERA5), building energy
benchmarks (ENERGY STAR), environmental disclosures (CDP open data),
toxic-release tracking (EPA TRI + Superfund), and nuclear regulatory
oversight (NRC inspections).

Sources land with D5 (Q2) and feed Property (A2), Energy (A8),
Env Liability (B4), and Crop (B10) coverages.
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


def _text(url: str, *, timeout: float = 6.0):
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "dsi/1.0"},
    ) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


class _ClimateBase(ProductionExtractor):
    COST_TIER = "free"

    def get_required_config(self) -> List[str]:
        return []


class FEMAFloodExtractor(_ClimateBase):
    SOURCE_NAME = "climate.fema_flood"
    DEFAULT_TTL_SECONDS = 7_776_000  # quarterly
    KILL_SWITCH_ENV = "DSI_DISABLE_FEMA_FLOOD"

    # V6/Stage-6 field-depth expansion.
    # Parses the NFHL service descriptor for: layer names (A / AE / V /
    # X zones surfaced), spatial-reference, current status — useful for
    # callers resolving specific flood zone lookups downstream.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json(
                "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer?f=json"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        layers = data.get("layers", []) if isinstance(data, dict) else []
        layer_names = [l.get("name", "") for l in layers]
        zone_layer_hits = sum(
            1 for name in layer_names
            if any(kw in name.lower() for kw in ["flood", "zone", "hazard", "bfe"])
        )
        return self._create_success_result({
            "nfhl_service_reachable": bool(data),
            "service_layers": len(layers),
            "layer_names_sample": layer_names[:10],
            "zone_layer_hits": zone_layer_hits,
            "current_version": (data.get("currentVersion") if isinstance(data, dict) else ""),
            "spatial_reference_wkid": (
                ((data.get("spatialReference") or {}).get("latestWkid")
                 or (data.get("spatialReference") or {}).get("wkid"))
                if isinstance(data, dict) else None
            ),
        })


class NOAACDOExtractor(_ClimateBase):
    SOURCE_NAME = "climate.noaa_cdo"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_NOAA_CDO"
    API_KEY_ENV = "NOAA_CDO_TOKEN"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        token = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                "https://www.ncei.noaa.gov/cdo-web/api/v2/datasets",
                headers={"token": token},
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "dataset_count": len(data.get("results", []) if isinstance(data, dict) else []),
        })


class USFSFireHazardExtractor(_ClimateBase):
    SOURCE_NAME = "climate.usfs_fire_hazard"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_USFS_FIRE"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://apps.fs.usda.gov/arcx/rest/services/RDW_Wildfire/RMRS_WildfireHazardPotential_2020/MapServer?f=json")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class USGSSeismicExtractor(_ClimateBase):
    SOURCE_NAME = "climate.usgs_seismic"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_USGS_SEISMIC"

    # V6/Stage-6 field-depth expansion.
    # Returns magnitude-bucketed quake counts since 2024 (M5+, M6+,
    # M7+) plus most-recent significant event info from the FDSN
    # event feed.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        buckets: dict[str, int | None] = {}
        for mag in (5, 6, 7):
            try:
                data = _json(
                    "https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson"
                    f"&minmagnitude={mag}&starttime=2024-01-01"
                )
                buckets[f"m{mag}plus_since_2024"] = (
                    data.get("count") if isinstance(data, dict) else None
                )
            except httpx.HTTPError:
                buckets[f"m{mag}plus_since_2024"] = None

        # Latest significant event
        most_recent = {}
        try:
            recent = _json(
                "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
                "&limit=1&orderby=time&minmagnitude=6"
            )
            features = recent.get("features", []) if isinstance(recent, dict) else []
            if features:
                props = features[0].get("properties", {}) or {}
                most_recent = {
                    "mag": props.get("mag"),
                    "place": props.get("place"),
                    "time_ms": props.get("time"),
                }
        except httpx.HTTPError:
            pass

        return self._create_success_result({
            **buckets,
            "most_recent_m6plus": most_recent,
        })


class CopernicusSentinelExtractor(_ClimateBase):
    SOURCE_NAME = "climate.copernicus_sentinel"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_COPERNICUS"
    API_KEY_ENV = "SENTINELHUB_CLIENT_ID"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Sentinel Hub imagery requires OAuth2 — we ship a reachability
        # probe so the framework operates without imagery ingestion.
        try:
            data = _json("https://services.sentinel-hub.com/api/v1/configuration/products")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"catalog_reachable": bool(data)})


class ECMWFERA5Extractor(_ClimateBase):
    SOURCE_NAME = "climate.ecmwf_era5"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ERA5"
    API_KEY_ENV = "CDSAPI_KEY"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # ECMWF Climate Data Store needs OAuth + heavy downloads;
        # V6 ships an auth-free docs probe.
        try:
            txt = _text("https://cds.climate.copernicus.eu/api")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"cds_reachable": bool(txt)})


class CDPOpenDataExtractor(_ClimateBase):
    SOURCE_NAME = "climate.cdp_open"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_CDP"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            txt = _text(f"https://www.cdp.net/en/responses?queries%5Bname%5D={q}")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "mentions_company": q.lower() in txt.lower(),
        })


class ENERGYSTARExtractor(_ClimateBase):
    SOURCE_NAME = "climate.energystar"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ENERGYSTAR"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json(
                "https://data.energystar.gov/resource/58v3-c8sz.json?$limit=1"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "building_records_probe": len(data) if isinstance(data, list) else 0,
        })


class TRIExtractor(_ClimateBase):
    SOURCE_NAME = "climate.epa_tri"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_TRI"

    # V6/Stage-6 field-depth expansion.
    # Returns facility hit list plus per-state + per-industry-code
    # distribution + EPA registry IDs for the top 10 matches.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter
        q = self._normalize_domain(entity_id).split(".")[0]
        try:
            data = _json(
                f"https://data.epa.gov/efservice/tri_facility/facility_name/beginning/{q}/rows/0:25/json"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        rows = data if isinstance(data, list) else []
        state_counter: Counter = Counter()
        industry_counter: Counter = Counter()
        registry_ids: list[str] = []
        for r in rows:
            state = r.get("state_abbr") or r.get("STATE") or ""
            if state:
                state_counter[state] += 1
            industry = r.get("industry_sector") or r.get("PRIMARY_SIC_CODE") or ""
            if industry:
                industry_counter[str(industry)[:30]] += 1
            rid = r.get("trifid") or r.get("TRIFID") or ""
            if rid:
                registry_ids.append(str(rid))
        return self._create_success_result({
            "facility_count": len(rows),
            "state_distribution": dict(state_counter.most_common(5)),
            "industry_top": industry_counter.most_common(5),
            "trifid_sample": registry_ids[:10],
        })


class SuperfundExtractor(_ClimateBase):
    SOURCE_NAME = "climate.epa_superfund"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_SUPERFUND"

    # V6/Stage-6 field-depth expansion.
    # Returns total active-site count + state distribution + NPL status
    # summary from the SEMS active-sites endpoint.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        from collections import Counter
        try:
            data = _json(
                "https://data.epa.gov/efservice/SEMS_ACTIVE_SITES/rows/0:500/json"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        rows = data if isinstance(data, list) else []
        state_counter: Counter = Counter()
        npl_counter: Counter = Counter()
        for r in rows:
            state = r.get("state") or r.get("STATE") or ""
            if state:
                state_counter[state] += 1
            npl = r.get("npl_status") or r.get("NPL_STATUS_NAME") or ""
            if npl:
                npl_counter[str(npl)[:30]] += 1
        return self._create_success_result({
            "probe_ok": True,
            "sample_size": len(rows),
            "state_top": state_counter.most_common(5),
            "npl_status_top": npl_counter.most_common(5),
        })


class NRCInspectionExtractor(_ClimateBase):
    SOURCE_NAME = "climate.nrc_inspections"
    DEFAULT_TTL_SECONDS = 7_776_000
    KILL_SWITCH_ENV = "DSI_DISABLE_NRC"

    # V6/Stage-6 field-depth expansion.
    # Parses the tritium plant-info HTML for: plant count, state
    # breakdown, "in operation" vs "decommissioned" hit-counts.
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        import re
        from collections import Counter
        try:
            txt = _text(
                "https://www.nrc.gov/reactors/operating/ops-experience/tritium/plant-info.html"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))

        # Naive state extractor — 2-letter codes after a comma.
        state_counter: Counter = Counter(re.findall(r",\s*([A-Z]{2})\b", txt or ""))
        operating_hits = len(re.findall(r"in operation", txt or "", re.IGNORECASE))
        decom_hits = len(re.findall(r"decommission", txt or "", re.IGNORECASE))
        plant_hits = len(re.findall(r"Nuclear Power Plant", txt or "", re.IGNORECASE))
        return self._create_success_result({
            "reachable": bool(txt),
            "plant_name_mentions": plant_hits,
            "state_top": state_counter.most_common(5),
            "in_operation_hits": operating_hits,
            "decommissioned_hits": decom_hits,
        })
