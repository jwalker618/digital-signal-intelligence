"""V6/A5 maturation — new FI inference functions.

Scaffolded inference functions for Stage 4.8 — bank/insurer/fintech/
crypto depth per the A5 spec. All return neutral SignalResult(score=500);
extractor-backed bodies wire in once FFIEC / NAIC / blockchain-explorer
extractors ship in Stage 6.
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
        score=500.0,
        confidence=PROXY_TIER_CONFIDENCE.get(proxy_tier, 0.5),
        execution_time_ms=0.0,
    )


# ---- Bank -----------------------------------------------------------

@register_inference_function("ffiec_call_report_ratios_basefunction")
async def fi_a5_bank_01(entity_id: str, context: Any) -> SignalResult:
    """FFIEC Call Report key ratios (Texas ratio, NPL, Tier 1 leverage)."""
    return _neutral("ffiec_call_report_ratios", "DIRECT_OBSERVABLE")

@register_inference_function("ubpr_roe_volatility_basefunction")
async def fi_a5_bank_02(entity_id: str, context: Any) -> SignalResult:
    """UBPR ROE volatility over rolling 5-year quarterly window."""
    return _neutral("ubpr_roe_volatility", "DIRECT_OBSERVABLE")

@register_inference_function("bsa_aml_enforcement_basefunction")
async def fi_a5_bank_03(entity_id: str, context: Any) -> SignalResult:
    """FinCEN / OCC / Fed BSA-AML enforcement action record."""
    return _neutral("bsa_aml_enforcement", "DIRECT_OBSERVABLE")

@register_inference_function("cra_rating_basefunction")
async def fi_a5_bank_04(entity_id: str, context: Any) -> SignalResult:
    """Community Reinvestment Act rating (Outstanding/Satisfactory/Needs/Sub)."""
    return _neutral("cra_rating", "DIRECT_OBSERVABLE")

@register_inference_function("camels_proxy_composite_basefunction")
async def fi_a5_bank_05(entity_id: str, context: Any) -> SignalResult:
    """CAMELS-style proxy composite from public call-report ratios."""
    return _neutral("camels_proxy_composite", "INFERRED_PROXY")

@register_inference_function("dfast_ccar_outcome_basefunction")
async def fi_a5_bank_06(entity_id: str, context: Any) -> SignalResult:
    """DFAST / CCAR stress-test outcome (pass/conditional/restrictions)."""
    return _neutral("dfast_ccar_outcome", "DIRECT_OBSERVABLE")


# ---- Insurer --------------------------------------------------------

@register_inference_function("naic_rbc_band_basefunction")
async def fi_a5_ins_01(entity_id: str, context: Any) -> SignalResult:
    """NAIC Risk-Based Capital band (No Action / Trend / Company / Regulatory / Authorized)."""
    return _neutral("naic_rbc_band", "DIRECT_OBSERVABLE")

@register_inference_function("iris_ratio_band_basefunction")
async def fi_a5_ins_02(entity_id: str, context: Any) -> SignalResult:
    """NAIC IRIS ratio-usual-range exceptions count."""
    return _neutral("iris_ratio_band", "DIRECT_OBSERVABLE")

@register_inference_function("complaint_index_basefunction")
async def fi_a5_ins_03(entity_id: str, context: Any) -> SignalResult:
    """State-DOI complaint index (actual vs expected complaint count)."""
    return _neutral("complaint_index", "DIRECT_OBSERVABLE")

@register_inference_function("jiri_index_basefunction")
async def fi_a5_ins_04(entity_id: str, context: Any) -> SignalResult:
    """Justified Insurance Regulatory Intervention index (composite of RBC + IRIS + complaints)."""
    return _neutral("jiri_index", "INFERRED_PROXY")


# ---- Fintech --------------------------------------------------------

@register_inference_function("sponsor_bank_dependency_basefunction")
async def fi_a5_ft_01(entity_id: str, context: Any) -> SignalResult:
    """Dependency profile on sponsor-bank (single-point-of-failure risk)."""
    return _neutral("sponsor_bank_dependency", "INFERRED_PROXY")

@register_inference_function("bsa_findings_velocity_basefunction")
async def fi_a5_ft_02(entity_id: str, context: Any) -> SignalResult:
    """BSA finding velocity from sponsor-bank exam cycles (public OCC feed)."""
    return _neutral("bsa_findings_velocity", "INFERRED_PROXY")

@register_inference_function("complaint_velocity_basefunction")
async def fi_a5_ft_03(entity_id: str, context: Any) -> SignalResult:
    """CFPB complaint velocity (count/month normalized to active users)."""
    return _neutral("complaint_velocity", "DIRECT_OBSERVABLE")


# ---- Crypto ---------------------------------------------------------

@register_inference_function("ofac_exposure_proxy_basefunction")
async def fi_a5_cr_01(entity_id: str, context: Any) -> SignalResult:
    """OFAC SDN wallet address interaction proxy via public explorers."""
    return _neutral("ofac_exposure_proxy", "INFERRED_PROXY")

@register_inference_function("mixer_tumbler_interaction_basefunction")
async def fi_a5_cr_02(entity_id: str, context: Any) -> SignalResult:
    """Known mixer / tumbler interaction volume (heuristic clustering)."""
    return _neutral("mixer_tumbler_interaction", "INFERRED_PROXY")

@register_inference_function("travel_rule_compliance_basefunction")
async def fi_a5_cr_03(entity_id: str, context: Any) -> SignalResult:
    """Travel Rule Protocol directory membership + attestation status."""
    return _neutral("travel_rule_compliance", "INFERRED_PROXY")

@register_inference_function("reserve_attestation_cadence_basefunction")
async def fi_a5_cr_04(entity_id: str, context: Any) -> SignalResult:
    """Independent reserve attestation cadence + auditor reputation."""
    return _neutral("reserve_attestation_cadence", "INFERRED_PROXY")

@register_inference_function("cex_dex_exposure_mix_basefunction")
async def fi_a5_cr_05(entity_id: str, context: Any) -> SignalResult:
    """CEX vs DEX volume mix — operational-risk differentiator."""
    return _neutral("cex_dex_exposure_mix", "INFERRED_PROXY")
