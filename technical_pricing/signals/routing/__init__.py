"""
DSI Signal Routing Module

This module provides jurisdiction-aware routing for signal extraction,
directing queries to the appropriate regional/global data sources.

Components:
    Router:
        - JurisdictionRouter: Routes entities to appropriate extractors by locale
        - ExtractorGroup: Defines groups of extractors by signal type
        - RoutingStrategy: Configures how extractors are selected

    Schemas:
        - SanctionsResult, SanctionsMatch: Unified sanctions output
        - CorporateResult, CorporateRecord: Unified corporate registry output
        - RegulatoryResult, RegulatoryViolation: Unified regulatory output
        - DomainResult, DomainRecord: Unified domain/WHOIS output

    Aggregators:
        - SanctionsAggregator: Multi-source sanctions check
        - CorporateAggregator: Multi-source corporate lookup

Usage:
    # Simple routing - get list of extractors
    from technical_pricing.signals.routing import JurisdictionRouter, RoutingStrategy

    router = JurisdictionRouter()
    extractors = router.get_extractors(
        signal_type='sanctions',
        locale='UK',
        strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL
    )
    # Returns: ['uk_ofsi', 'opensanctions', 'interpol_red_notices', ...]

    # Full aggregation - call extractors and consolidate results
    from technical_pricing.signals.routing import SanctionsAggregator

    aggregator = SanctionsAggregator()
    result = aggregator.aggregate(
        entity_id='Acme Corporation',
        signal_type='sanctions',
        locale='UK'
    )
    print(f"Risk: {result.result.risk_level}")
    print(f"Matches: {result.result.total_matches}")
"""

# Router components
from .router import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    ExtractorGroup,
    JURISDICTION_MAPPINGS,
    TLD_TO_LOCALE,
    EXTRACTOR_TIERS,
)

# Unified schemas
from .schemas import (
    # Enums
    SanctionsMatchType,
    SanctionsProgram,
    RiskLevel,
    # Sanctions
    SanctionsMatch,
    SanctionsResult,
    # Corporate
    CorporateRecord,
    CorporateResult,
    # Regulatory
    RegulatoryViolation,
    RegulatoryResult,
    # Domain
    DomainRecord,
    DomainResult,
    # Registry
    SIGNAL_SCHEMAS,
    get_schema,
)

# Multi-source aggregation
from .multi_source import (
    MultiSourceAggregator,
    MultiSourceResult,
    ExtractorCallResult,
    calculate_risk_level,
)

# Concrete aggregators
from .sanctions_aggregator import SanctionsAggregator
from .corporate_aggregator import CorporateAggregator

__all__ = [
    # Router
    'JurisdictionRouter',
    'RoutingStrategy',
    'ExtractorTier',
    'ExtractorGroup',
    'JURISDICTION_MAPPINGS',
    'TLD_TO_LOCALE',
    'EXTRACTOR_TIERS',
    # Schemas - Enums
    'SanctionsMatchType',
    'SanctionsProgram',
    'RiskLevel',
    # Schemas - Sanctions
    'SanctionsMatch',
    'SanctionsResult',
    # Schemas - Corporate
    'CorporateRecord',
    'CorporateResult',
    # Schemas - Regulatory
    'RegulatoryViolation',
    'RegulatoryResult',
    # Schemas - Domain
    'DomainRecord',
    'DomainResult',
    # Schema registry
    'SIGNAL_SCHEMAS',
    'get_schema',
    # Multi-source
    'MultiSourceAggregator',
    'MultiSourceResult',
    'ExtractorCallResult',
    'calculate_risk_level',
    # Aggregators
    'SanctionsAggregator',
    'CorporateAggregator',
]
