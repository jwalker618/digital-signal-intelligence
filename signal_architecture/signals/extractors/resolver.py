"""
DSI Extractor Resolver

Provides a unified interface for inference functions to obtain extractors.
Routes through the factory when available, falls back to direct stub imports.

Usage in inference functions:
    from ....extractors.resolver import get_extractor

    extractor = get_extractor("email_auth")
    result = extractor.extract(entity_id, context=context)
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Map from factory name -> (stub module path, stub class name)
# This allows the resolver to fall back to stubs if the factory doesn't
# have the extractor registered.
_CYBER_STUB_MAP: Dict[str, tuple] = {
    # Network Authority
    "certification_authority": ("stubs.cyber", "CertificationAuthorityExtractor"),
    "cloud_infra": ("stubs.cyber", "CloudInfraExtractor"),
    "customer_quality": ("stubs.cyber", "CustomerQualityExtractor"),
    "financial_relationship": ("stubs.cyber", "FinancialRelationshipExtractor"),
    "partner_network": ("stubs.cyber", "PartnerNetworkExtractor"),
    "network_centrality": ("stubs.cyber", "NetworkCentralityExtractor"),
    "second_degree": ("stubs.cyber", "SecondDegreeExtractor"),
    # Technical Infrastructure
    "dnssec": ("stubs.cyber", "DNSSECExtractor"),
    "tls_config": ("stubs.cyber", "TLSConfigExtractor"),
    "email_auth": ("stubs.cyber", "EmailAuthExtractor"),
    "security_headers": ("stubs.cyber", "SecurityHeadersExtractor"),
    "waf_presence": ("stubs.cyber", "WAFPresenceExtractor"),
    "cdn_usage": ("stubs.cyber", "CDNUsageExtractor"),
    "security_txt": ("stubs.cyber", "SecurityTxtExtractor"),
    "bug_bounty": ("stubs.cyber", "BugBountyExtractor"),
    "cve_exposure": ("stubs.cyber", "CVEExposureExtractor"),
    "network_exposure": ("stubs.cyber", "NetworkExposureExtractor"),
    "software_currency": ("stubs.cyber", "SoftwareCurrencyExtractor"),
    # Corporate Footprint
    "credential_exposure": ("stubs.cyber", "CredentialExposureExtractor"),
    "dark_web": ("stubs.cyber", "DarkWebExtractor"),
    "security_page": ("stubs.cyber", "SecurityPageExtractor"),
    "technical_content": ("stubs.cyber", "TechnicalContentExtractor"),
    "developer_resources": ("stubs.cyber", "DeveloperResourcesExtractor"),
    "security_hiring": ("stubs.cyber", "SecurityHiringExtractor"),
    "security_leadership": ("stubs.cyber", "SecurityLeadershipExtractor"),
    "security_vendor": ("stubs.cyber", "SecurityVendorExtractor"),
    "compliance_badges": ("stubs.cyber", "ComplianceBadgesExtractor"),
    "privacy_policy": ("stubs.cyber", "PrivacyPolicyExtractor"),
    # Public Record
    "breach_history": ("stubs.cyber", "BreachHistoryExtractor"),
    "litigation_history": ("stubs.cyber", "LitigationHistoryExtractor"),
    "security_rating": ("stubs.cyber", "SecurityRatingExtractor"),
    "esg_cyber": ("stubs.cyber", "ESGCyberExtractor"),
    # Categorical
    "industry_classification": ("stubs.cyber", "IndustryClassificationExtractor"),
    "company_size": ("stubs.cyber", "CompanySizeExtractor"),
    "operational_base": ("stubs.cyber", "OperationalBaseExtractor"),
    # Common
    "credit_rating": ("stubs.common", "CreditRatingExtractor"),
}

# Cache of resolved stub classes
_stub_cache: Dict[str, Any] = {}


def _get_mode() -> str:
    """Get the current extractor mode from environment or factory default."""
    # Check environment first
    env_mode = os.getenv("DSI_EXTRACTOR_MODE")
    if env_mode:
        return env_mode

    # Check FEATURE_USE_STUBS (API-level flag)
    use_stubs = os.getenv("FEATURE_USE_STUBS", "true").lower()
    if use_stubs == "false":
        return "hybrid"

    return "stub"


def _resolve_stub(name: str) -> Any:
    """Resolve a stub extractor class by factory name."""
    if name in _stub_cache:
        return _stub_cache[name]

    mapping = _CYBER_STUB_MAP.get(name)
    if mapping is None:
        return None

    module_path, class_name = mapping
    try:
        import importlib
        full_path = f"signal_architecture.signals.extractors.{module_path}"
        mod = importlib.import_module(full_path)
        cls = getattr(mod, class_name)
        _stub_cache[name] = cls
        return cls
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not resolve stub extractor '{name}': {e}")
        return None


def get_extractor(name: str, mode: Optional[str] = None) -> Any:
    """
    Get an extractor instance by name.

    Tries the factory first (for production/hybrid mode), falls back
    to direct stub instantiation.

    Args:
        name: Extractor name (e.g., 'email_auth', 'tls_config')
        mode: Override mode ('stub', 'production', 'hybrid')

    Returns:
        Extractor instance ready to call .extract()
    """
    effective_mode = mode or _get_mode()

    # Try factory for non-stub modes
    if effective_mode in ("production", "hybrid"):
        try:
            from .production.factory import get_extractor as factory_get
            return factory_get(name, mode=effective_mode)
        except (ImportError, ValueError) as e:
            if effective_mode == "production":
                raise
            logger.debug(f"Factory lookup failed for '{name}', falling back to stub: {e}")

    # Fall back to stub
    stub_class = _resolve_stub(name)
    if stub_class is not None:
        return stub_class()

    raise ValueError(f"No extractor found for '{name}' (mode={effective_mode})")


def register_stubs_with_factory() -> int:
    """
    Register all known stub extractors with the factory registry.

    Call this at startup so the factory can use stubs as fallbacks
    in hybrid mode.

    Returns:
        Number of stubs registered.
    """
    try:
        from .production.factory import register_stub
    except ImportError:
        logger.warning("Factory not available, skipping stub registration")
        return 0

    count = 0
    for name in _CYBER_STUB_MAP:
        stub_class = _resolve_stub(name)
        if stub_class is not None:
            try:
                register_stub(name, stub_class)
                count += 1
            except Exception as e:
                logger.debug(f"Could not register stub '{name}': {e}")

    logger.info(f"Registered {count} stub extractors with factory")
    return count
