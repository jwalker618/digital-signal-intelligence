"""V6/A7 maturation — new Marine inference functions.

Scaffolded inference functions for Stage 4.10. All return neutral
SignalResult(score=50.0); real bodies wire in once AIS Hub, Marine
Cadastre, EMSA THETIS, Paris MoU, Tokyo MoU, IMO GISIS deep-field
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
        score=50.0,
        confidence=PROXY_TIER_CONFIDENCE.get(proxy_tier, 0.5),
        execution_time_ms=0.0,
    )


@register_inference_function("ais_dark_activity_rate_basefunction")
def marine_a7_01(entity_id: str, context: Any) -> SignalResult:
    """AIS dark-activity rate (transponder gaps / sanctions evasion proxy)."""
    return _neutral("ais_dark_activity_rate", "INFERRED_PROXY")

@register_inference_function("ais_spoofing_signal_basefunction")
def marine_a7_02(entity_id: str, context: Any) -> SignalResult:
    """AIS spoofing indicators (impossible speed / location)."""
    return _neutral("ais_spoofing_signal", "INFERRED_PROXY")

@register_inference_function("paris_mou_detention_history_basefunction")
def marine_a7_03(entity_id: str, context: Any) -> SignalResult:
    """Paris MoU detention history — Port State Control performance."""
    return _neutral("paris_mou_detention_history", "DIRECT_OBSERVABLE")

@register_inference_function("tokyo_mou_detention_history_basefunction")
def marine_a7_04(entity_id: str, context: Any) -> SignalResult:
    """Tokyo MoU detention history — Asia-Pacific PSC performance."""
    return _neutral("tokyo_mou_detention_history", "DIRECT_OBSERVABLE")

@register_inference_function("class_society_transfer_frequency_basefunction")
def marine_a7_05(entity_id: str, context: Any) -> SignalResult:
    """Classification society transfer frequency — class-shopping proxy."""
    return _neutral("class_society_transfer_frequency", "INFERRED_PROXY")

@register_inference_function("imo_cic_campaign_results_basefunction")
def marine_a7_06(entity_id: str, context: Any) -> SignalResult:
    """IMO Concentrated Inspection Campaign results (thematic inspection)."""
    return _neutral("imo_cic_campaign_results", "DIRECT_OBSERVABLE")

@register_inference_function("flag_of_convenience_proxy_basefunction")
def marine_a7_07(entity_id: str, context: Any) -> SignalResult:
    """Flag of convenience proxy from ITF + Paris MoU black/grey/white lists."""
    return _neutral("flag_of_convenience_proxy", "INFERRED_PROXY")

@register_inference_function("sts_transfer_density_basefunction")
def marine_a7_08(entity_id: str, context: Any) -> SignalResult:
    """Ship-to-ship transfer density — sanctions / pollution exposure proxy."""
    return _neutral("sts_transfer_density", "INFERRED_PROXY")

@register_inference_function("piracy_corridor_exposure_basefunction")
def marine_a7_09(entity_id: str, context: Any) -> SignalResult:
    """Piracy corridor exposure from IMB Piracy Reporting Centre + AIS routes."""
    return _neutral("piracy_corridor_exposure", "INFERRED_PROXY")

@register_inference_function("vessel_age_profile_curve_basefunction")
def marine_a7_10(entity_id: str, context: Any) -> SignalResult:
    """Vessel age-profile curve (full distribution, not single mean)."""
    return _neutral("vessel_age_profile_curve", "INFERRED_PROXY")
