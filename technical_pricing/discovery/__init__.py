"""
DSI Discovery Module

Provides entity identification and website discovery functionality.
This module is used as a pre-processing step before the pricing workflow
to identify the correct corporate website for signal extraction.

Usage:
    from technical_pricing.discovery import discover_website, WebsiteDiscoveryEngine

    # Simple discovery
    result = discover_website("MS Amlin")
    print(result.primary_website.domain)

    # Discovery with hints
    result = discover_website(
        "Petrobras",
        domain_hint="petrobras.com.br",
        country_hint="Brazil"
    )
"""

from .website_discovery import (
    # Main classes
    WebsiteDiscoveryEngine,
    BatchWebsiteDiscovery,
    # Data structures
    DiscoveryResult,
    WebsiteCandidate,
    CompanyIdentity,
    DomainInfo,
    CorporateRelationship,
    # Enums
    DiscoveryMethod,
    ConfidenceLevel,
    WebsiteType,
    CompanyStructure,
    # Convenience functions
    discover_website,
    validate_corporate_domain,
)

__all__ = [
    # Main classes
    "WebsiteDiscoveryEngine",
    "BatchWebsiteDiscovery",
    # Data structures
    "DiscoveryResult",
    "WebsiteCandidate",
    "CompanyIdentity",
    "DomainInfo",
    "CorporateRelationship",
    # Enums
    "DiscoveryMethod",
    "ConfidenceLevel",
    "WebsiteType",
    "CompanyStructure",
    # Convenience functions
    "discover_website",
    "validate_corporate_domain",
]
