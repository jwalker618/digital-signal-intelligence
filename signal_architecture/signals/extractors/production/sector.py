"""V6/D6 — Sector telemetry extractors.

Aviation (OpenSky, ICAO registry, ASIAS), maritime deep-dive (AIS Hub,
Marine Cadastre, EMSA THETIS, Paris + Tokyo MoU), and energy-asset
telemetry (PHMSA, BSEE detail, NERC violations).

Consumed by Aerospace (A6), Marine (A7), Energy (A8),
Environmental Liability (B4).
"""
from __future__ import annotations

import os
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

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            data = _json("https://opensky-network.org/api/states/all?time=0")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        states = data.get("states") if isinstance(data, dict) else None
        return self._create_success_result({
            "states_returned": len(states) if states else 0,
        })


class ICAORegistryExtractor(_SectorBase):
    SOURCE_NAME = "sector.icao_registry"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ICAO"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.icao.int/publications/Pages/doc7300.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class ASIASExtractor(_SectorBase):
    SOURCE_NAME = "sector.asias"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_ASIAS"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.asias.faa.gov/apex/f?p=100:1:0::NO:::")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


# ---------------------------------------------------------------------------
# Maritime deep-dive
# ---------------------------------------------------------------------------

class AISHubExtractor(_SectorBase):
    SOURCE_NAME = "sector.ais_hub"
    DEFAULT_TTL_SECONDS = 3_600
    KILL_SWITCH_ENV = "DSI_DISABLE_AIS_HUB"
    API_KEY_ENV = "AIS_HUB_API_KEY"
    COST_TIER = "low"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        key = os.environ[self.API_KEY_ENV]
        try:
            data = _json(
                f"https://data.aishub.net/ws.php?username={key}&format=1&output=json"
            )
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({
            "ship_rows_probe": len(data[1]) if isinstance(data, list) and len(data) > 1 else 0,
        })


class MarineCadastreExtractor(_SectorBase):
    SOURCE_NAME = "sector.marine_cadastre"
    DEFAULT_TTL_SECONDS = 86_400
    KILL_SWITCH_ENV = "DSI_DISABLE_MARINE_CADASTRE"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://marinecadastre.gov/ais/")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class EMSAExtractor(_SectorBase):
    SOURCE_NAME = "sector.emsa_thetis"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_EMSA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://portal.emsa.europa.eu/web/thetis-mrv")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class ParisMoUExtractor(_SectorBase):
    SOURCE_NAME = "sector.paris_mou"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_PARIS_MOU"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://parismou.org/inspection-search")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class TokyoMoUExtractor(_SectorBase):
    SOURCE_NAME = "sector.tokyo_mou"
    DEFAULT_TTL_SECONDS = 604_800
    KILL_SWITCH_ENV = "DSI_DISABLE_TOKYO_MOU"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.tokyo-mou.org/inspections_detentions/psc_database.php")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


# ---------------------------------------------------------------------------
# Energy assets
# ---------------------------------------------------------------------------

class PHMSAExtractor(_SectorBase):
    SOURCE_NAME = "sector.phmsa"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_PHMSA"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.phmsa.dot.gov/data-and-statistics/pipeline/incident-statistics")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class BSEEDetailExtractor(_SectorBase):
    SOURCE_NAME = "sector.bsee_detail"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_BSEE"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.data.bsee.gov/Main/Incidents.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})


class NERCVioExtractor(_SectorBase):
    SOURCE_NAME = "sector.nerc_violations"
    DEFAULT_TTL_SECONDS = 2_592_000
    KILL_SWITCH_ENV = "DSI_DISABLE_NERC"

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        try:
            txt = _text("https://www.nerc.com/pa/comp/ce/Pages/default.aspx")
        except httpx.HTTPError as e:
            return self._create_error_result(str(e))
        return self._create_success_result({"reachable": bool(txt)})
