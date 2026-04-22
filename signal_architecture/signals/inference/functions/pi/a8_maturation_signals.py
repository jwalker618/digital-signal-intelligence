"""V6/A8 maturation — new PI inference functions (clinical + media-tech).

Scaffolded inference functions for Stage 4.11. `pi_clinical_research`
and `pi_media_tech` sub-configs are deferred to A8-deep; these
signals live in existing sub-configs for now.
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


@register_inference_function("irb_registration_basefunction")
def pi_a8_01(entity_id: str, context: Any) -> SignalResult:
    """OHRP / FDA IRB registration status + coverage scope."""
    return _neutral("irb_registration", "DIRECT_OBSERVABLE")

@register_inference_function("clinical_trial_registry_compliance_basefunction")
def pi_a8_02(entity_id: str, context: Any) -> SignalResult:
    """ClinicalTrials.gov registration + results-reporting compliance."""
    return _neutral("clinical_trial_registry_compliance", "DIRECT_OBSERVABLE")

@register_inference_function("good_clinical_practice_score_basefunction")
def pi_a8_03(entity_id: str, context: Any) -> SignalResult:
    """Good Clinical Practice compliance posture (ICH E6 adherence)."""
    return _neutral("good_clinical_practice_score", "INFERRED_PROXY")

@register_inference_function("defamation_exposure_basefunction")
def pi_a8_04(entity_id: str, context: Any) -> SignalResult:
    """Defamation exposure proxy from CourtListener + published content."""
    return _neutral("defamation_exposure", "INFERRED_PROXY")

@register_inference_function("content_moderation_posture_basefunction")
def pi_a8_05(entity_id: str, context: Any) -> SignalResult:
    """Content moderation policy + transparency report cadence."""
    return _neutral("content_moderation_posture", "INFERRED_PROXY")
