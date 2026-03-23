"""
Routed Inference Functions

Pre-built inference functions that use the multi-source routing module
for comprehensive, jurisdiction-aware signal extraction.

These functions can be used directly in YAML configs:
    signal_features:
      - id: sanctions_check
        inference_utility_function: sanctions_check_routed

Or called directly:
    from signals.inference.functions.routed import (
        sanctions_check_routed,
        corporate_registry_routed,
    )

    result = sanctions_check_routed(entity_id='Acme Corp', context=context)
"""

from .signals import (
    # Sanctions & Corporate
    sanctions_check_routed,
    corporate_registry_routed,
    corporate_status_routed,
    corporate_age_routed,
    lei_verification_routed,
    # DNS
    email_auth_routed,
    dnssec_routed,
    domain_age_routed,
    # Network
    security_headers_routed,
    tls_config_routed,
    infrastructure_routed,
    # Security
    vulnerability_routed,
    breach_history_routed,
)

from ...registry import register_inference_function

__all__ = [
    # Sanctions & Corporate
    'sanctions_check_routed',
    'corporate_registry_routed',
    'corporate_status_routed',
    'corporate_age_routed',
    'lei_verification_routed',
    # DNS
    'email_auth_routed',
    'dnssec_routed',
    'domain_age_routed',
    # Network
    'security_headers_routed',
    'tls_config_routed',
    'infrastructure_routed',
    # Security
    'vulnerability_routed',
    'breach_history_routed',
    # Registration
    'register_all',
]


def register_all():
    """Register all routed inference functions with the registry."""
    # Sanctions & Corporate
    register_inference_function('sanctions_check_routed', sanctions_check_routed)
    register_inference_function('corporate_registry_routed', corporate_registry_routed)
    register_inference_function('corporate_status_routed', corporate_status_routed)
    register_inference_function('corporate_age_routed', corporate_age_routed)
    register_inference_function('lei_verification_routed', lei_verification_routed)
    # DNS
    register_inference_function('email_auth_routed', email_auth_routed)
    register_inference_function('dnssec_routed', dnssec_routed)
    register_inference_function('domain_age_routed', domain_age_routed)
    # Network
    register_inference_function('security_headers_routed', security_headers_routed)
    register_inference_function('tls_config_routed', tls_config_routed)
    register_inference_function('infrastructure_routed', infrastructure_routed)
    # Security
    register_inference_function('vulnerability_routed', vulnerability_routed)
    register_inference_function('breach_history_routed', breach_history_routed)
