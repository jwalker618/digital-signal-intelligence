"""
Routed Inference Functions

Pre-built inference functions that use the multi-source routing module
for comprehensive, jurisdiction-aware signal extraction.

These functions can be used directly in YAML configs:
    signal_features:
      - id: sanctions_check
        inference_utility_function: sanctions_check_routed

Or called directly:
    from technical_pricing.signals.inference.functions.routed import (
        sanctions_check_routed,
        corporate_registry_routed,
    )

    result = sanctions_check_routed(entity_id='Acme Corp', context=context)
"""

from .signals import (
    sanctions_check_routed,
    corporate_registry_routed,
    corporate_status_routed,
    corporate_age_routed,
    lei_verification_routed,
)

from ..registry import register_inference_function

__all__ = [
    'sanctions_check_routed',
    'corporate_registry_routed',
    'corporate_status_routed',
    'corporate_age_routed',
    'lei_verification_routed',
    'register_all',
]


def register_all():
    """Register all routed inference functions with the registry."""
    register_inference_function('sanctions_check_routed', sanctions_check_routed)
    register_inference_function('corporate_registry_routed', corporate_registry_routed)
    register_inference_function('corporate_status_routed', corporate_status_routed)
    register_inference_function('corporate_age_routed', corporate_age_routed)
    register_inference_function('lei_verification_routed', lei_verification_routed)
