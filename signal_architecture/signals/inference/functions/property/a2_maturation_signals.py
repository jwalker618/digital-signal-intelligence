"""V6/A2 maturation — new Property inference functions.

Scaffolded inference functions for Stage 4.5 signals:
FEMA flood zone, NOAA hail history, USFS wildfire hazard, USGS Vs30,
NHC track proximity, ISO CAF/BCEG code-compliance, ENERGY STAR score,
building permit trail, overhead imagery condition, NFIP participation.

All return neutral SignalResult(score=50.0). Real bodies wire in once
D5 ships FEMA NFHL / NOAA CDO / USFS WHP / USGS Vs30 / NHC historical-
track / ENERGY STAR / ISO CAF extractors.
"""
from __future__ import annotations

from typing import Any

from signal_architecture.signals.inference.registry import register_inference_function
from signal_architecture.signals.types import SignalResult


PROXY_TIER_CONFIDENCE = {
    "DIRECT_OBSERVABLE": 0.90,
    "INFERRED_PROXY":    0.70,
    "TRIANGULATED":      0.55,
    "DIRECT_INQUIRY":    0.40,
    "CORRELATIONAL":     0.30,
}


def _neutral(signal_id: str, proxy_tier: str) -> SignalResult:
    return SignalResult(
        signal_id=signal_id,
        score=50.0,
        confidence=PROXY_TIER_CONFIDENCE.get(proxy_tier, 0.5),
        execution_time_ms=0.0,
    )


@register_inference_function("fema_flood_zone_basefunction")
def property_a2_01(entity_id: str, context: Any) -> SignalResult:
    """FEMA NFHL flood-zone classification (A/AE/V/X) for the risk address."""
    return _neutral("fema_flood_zone", "DIRECT_OBSERVABLE")

@register_inference_function("noaa_hail_history_basefunction")
def property_a2_02(entity_id: str, context: Any) -> SignalResult:
    """NOAA SPC Storm Events: 25-year hail event frequency within 10 mi."""
    return _neutral("noaa_hail_history", "DIRECT_OBSERVABLE")

@register_inference_function("usfs_wildfire_hazard_basefunction")
def property_a2_03(entity_id: str, context: Any) -> SignalResult:
    """USFS Wildfire Hazard Potential raster value for the address parcel."""
    return _neutral("usfs_wildfire_hazard", "DIRECT_OBSERVABLE")

@register_inference_function("usgs_seismic_vs30_basefunction")
def property_a2_04(entity_id: str, context: Any) -> SignalResult:
    """USGS Vs30 shear-wave velocity (site-class proxy) for seismic exposure."""
    return _neutral("usgs_seismic_vs30", "DIRECT_OBSERVABLE")

@register_inference_function("nhc_track_proximity_basefunction")
def property_a2_05(entity_id: str, context: Any) -> SignalResult:
    """NHC historical hurricane track proximity (distance to centerline)."""
    return _neutral("nhc_track_proximity", "DIRECT_OBSERVABLE")

@register_inference_function("iso_caf_bceg_code_compliance_basefunction")
def property_a2_06(entity_id: str, context: Any) -> SignalResult:
    """ISO CAF / BCEG building-code enforcement rating for the jurisdiction."""
    return _neutral("iso_caf_bceg_code_compliance", "INFERRED_PROXY")

@register_inference_function("energy_star_score_basefunction")
def property_a2_07(entity_id: str, context: Any) -> SignalResult:
    """ENERGY STAR benchmarking score (proxy for systems quality + upkeep)."""
    return _neutral("energy_star_score", "INFERRED_PROXY")

@register_inference_function("building_permit_trail_basefunction")
def property_a2_08(entity_id: str, context: Any) -> SignalResult:
    """Jurisdictional permit-trail density — maintenance + upgrade cadence."""
    return _neutral("building_permit_trail", "INFERRED_PROXY")

@register_inference_function("overhead_imagery_condition_score_basefunction")
def property_a2_09(entity_id: str, context: Any) -> SignalResult:
    """Overhead-imagery-derived roof / grounds condition score."""
    return _neutral("overhead_imagery_condition_score", "INFERRED_PROXY")

@register_inference_function("nfip_participation_basefunction")
def property_a2_10(entity_id: str, context: Any) -> SignalResult:
    """FEMA CRS participation status (community-level flood-risk maturity)."""
    return _neutral("nfip_participation", "DIRECT_OBSERVABLE")
