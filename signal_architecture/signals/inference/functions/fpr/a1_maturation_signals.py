"""V6/A1 maturation — new FPR inference functions.

Scaffolded inference functions for the signals added by Stage 4.4:
ACLED incident density, WGI score, OFAC country tier, capital
controls watchlist, BIT treaty coverage, ACLED K&R rate, travel
pattern density, executive exposure footprint, buyer concentration,
sector credit spread.

All return neutral SignalResult(score=50.0). Real bodies wire in with
Stage 6 D-extractor depth — ACLED + World Bank WGI + OFAC lists are
already landed in D3/D5.
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
        evidence_grade="inferred",
        evidence_basis=f"Stub: neutral maturation scaffold (proxy_tier={proxy_tier})",
        evidence_sources=[],
    )


@register_inference_function("acled_incident_density_basefunction")
def fpr_a1_01(entity_id: str, context: Any) -> SignalResult:
    """ACLED armed-conflict / protest event density per country-sector pair"""
    return _neutral("acled_incident_density", "INFERRED_PROXY")

@register_inference_function("wb_wgi_score_basefunction")
def fpr_a1_02(entity_id: str, context: Any) -> SignalResult:
    """World Bank Worldwide Governance Indicators composite score"""
    return _neutral("wb_wgi_score", "DIRECT_OBSERVABLE")

@register_inference_function("ofac_country_tier_basefunction")
def fpr_a1_03(entity_id: str, context: Any) -> SignalResult:
    """OFAC country-sanctions tier (0-5)"""
    return _neutral("ofac_country_tier", "DIRECT_OBSERVABLE")

@register_inference_function("capital_controls_watchlist_basefunction")
def fpr_a1_04(entity_id: str, context: Any) -> SignalResult:
    """Capital controls watchlist membership (IMF AREAER)"""
    return _neutral("capital_controls_watchlist", "DIRECT_OBSERVABLE")

@register_inference_function("bit_treaty_coverage_basefunction")
def fpr_a1_05(entity_id: str, context: Any) -> SignalResult:
    """Bilateral Investment Treaty coverage between host and parent country"""
    return _neutral("bit_treaty_coverage", "DIRECT_OBSERVABLE")

@register_inference_function("acled_kfr_rate_country_basefunction")
def fpr_a1_06(entity_id: str, context: Any) -> SignalResult:
    """ACLED kidnapping event rate per capita"""
    return _neutral("acled_kfr_rate_country", "INFERRED_PROXY")

@register_inference_function("travel_pattern_density_basefunction")
def fpr_a1_07(entity_id: str, context: Any) -> SignalResult:
    """Derived executive travel-pattern density"""
    return _neutral("travel_pattern_density", "INFERRED_PROXY")

@register_inference_function("executive_exposure_footprint_basefunction")
def fpr_a1_08(entity_id: str, context: Any) -> SignalResult:
    """Executive travel + location footprint from public disclosures"""
    return _neutral("executive_exposure_footprint", "INFERRED_PROXY")

@register_inference_function("buyer_concentration_basefunction")
def fpr_a1_09(entity_id: str, context: Any) -> SignalResult:
    """Top-5-buyer concentration ratio from financials"""
    return _neutral("buyer_concentration", "DIRECT_OBSERVABLE")

@register_inference_function("sector_credit_spread_basefunction")
def fpr_a1_10(entity_id: str, context: Any) -> SignalResult:
    """FRED sector credit spread (OAS)"""
    return _neutral("sector_credit_spread", "DIRECT_OBSERVABLE")

