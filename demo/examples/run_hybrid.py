"""
Hybrid Mode Demo (Phase 15)

Demonstrates the new routed signal architecture with:
- Jurisdiction-aware multi-source extraction
- Routing-level caching
- Locale detection from domain/submission

This example shows how signals are routed to appropriate extractors
based on the entity's jurisdiction.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from signal_architecture.signals.routing import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    RoutingCache,
    get_routing_cache,
    set_routing_cache,
    EXTRACTOR_TIERS,
)
from signal_architecture.signals.aggregators.routing_bridges import (
    SanctionsSignalBridge,
    CorporateSignalBridge,
    DNSSignalBridge,
    NetworkSignalBridge,
    SecuritySignalBridge,
    get_bridge,
)
from signal_architecture.signals.types import InferenceContext


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def demo_jurisdiction_routing():
    """Demonstrate jurisdiction-aware routing."""
    print_header("JURISDICTION-AWARE ROUTING DEMO")

    router = JurisdictionRouter()

    # Test different locales
    test_cases = [
        ('sanctions', 'UK', 'British entity'),
        ('sanctions', 'US', 'American entity'),
        ('sanctions', 'DE', 'German entity'),
        ('corporate', 'UK', 'UK company'),
        ('corporate', 'AU', 'Australian company'),
        ('corporate', 'IN', 'Indian company'),
    ]

    for signal_type, locale, description in test_cases:
        extractors = router.get_extractors(
            signal_type=signal_type,
            locale=locale,
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
            max_tier=ExtractorTier.FREE,
        )
        print(f"{description} ({signal_type}, {locale}):")
        print(f"  Extractors: {', '.join(extractors[:5])}")
        if len(extractors) > 5:
            print(f"  ... and {len(extractors) - 5} more")
        print()


def demo_locale_detection():
    """Demonstrate locale detection from domain."""
    print_header("LOCALE DETECTION FROM DOMAIN")

    router = JurisdictionRouter()

    domains = [
        'acme.co.uk',
        'company.com.au',
        'firma.de',
        'enterprise.fr',
        'business.com',
        'corp.jp',
        'empresa.com.br',
    ]

    for domain in domains:
        locale = router.detect_locale_from_domain(domain)
        print(f"  {domain:25} -> {locale}")


def demo_routing_strategies():
    """Demonstrate different routing strategies."""
    print_header("ROUTING STRATEGIES")

    router = JurisdictionRouter()

    strategies = [
        (RoutingStrategy.LOCALE_ONLY, "LOCALE_ONLY - Only regional extractors"),
        (RoutingStrategy.GLOBAL_ONLY, "GLOBAL_ONLY - Only global extractors"),
        (RoutingStrategy.LOCALE_PLUS_GLOBAL, "LOCALE_PLUS_GLOBAL - Both regional + global"),
    ]

    for strategy, description in strategies:
        print(f"\n{description}:")
        extractors = router.get_extractors(
            signal_type='sanctions',
            locale='UK',
            strategy=strategy,
            max_tier=ExtractorTier.FREE,
        )
        print(f"  Sanctions extractors for UK: {len(extractors)}")
        print(f"  Examples: {', '.join(extractors[:3])}")


def demo_routing_cache():
    """Demonstrate routing-level caching."""
    print_header("ROUTING CACHE DEMO")

    # Create a fresh cache for demo
    cache = RoutingCache(default_ttl_seconds=300)
    set_routing_cache(cache)

    # Simulate caching some results
    print("Storing cached results...")
    cache.set('opensanctions', 'Test Corp', {'matches': [], 'checked': True})
    cache.set('ofac_sdn', 'Test Corp', {'matches': [], 'checked': True})
    cache.set('companies_house', 'Acme Ltd', {'status': 'Active', 'found': True})

    # Check cache stats
    print("\nCache after storing 3 entries:")
    stats = cache.get_stats()
    print(f"  Entries: {stats['current_entries']}")
    print(f"  Stores: {stats['stores']}")

    # Retrieve entries
    print("\nRetrieving from cache...")
    result1 = cache.get('opensanctions', 'Test Corp')
    print(f"  Get opensanctions:Test Corp -> {'HIT' if result1 else 'MISS'}")

    result2 = cache.get('opensanctions', 'Test Corp')  # Cache hit
    print(f"  Get opensanctions:Test Corp -> {'HIT' if result2 else 'MISS'}")

    result3 = cache.get('opensanctions', 'Unknown')    # Cache miss
    print(f"  Get opensanctions:Unknown   -> {'HIT' if result3 else 'MISS'}")

    print("\nCache statistics after 2 hits and 1 miss:")
    stats = cache.get_stats()
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate']:.1%}")

    # Invalidation demo
    print("\nInvalidating specific entry...")
    count = cache.invalidate('opensanctions', 'Test Corp')
    print(f"  Invalidated {count} entry")

    result = cache.get('opensanctions', 'Test Corp')
    print(f"  Get opensanctions:Test Corp -> {'HIT' if result else 'MISS'}")


def demo_bridge_aggregators():
    """Demonstrate bridge aggregators."""
    print_header("BRIDGE AGGREGATORS DEMO")

    # Get bridges for different signal types
    bridges = ['sanctions', 'corporate', 'dns', 'network', 'security']

    print("Available signal bridges:")
    for signal_type in bridges:
        bridge = get_bridge(signal_type)
        if bridge:
            print(f"  {signal_type:15} -> {type(bridge).__name__}")
        else:
            print(f"  {signal_type:15} -> Not available")

    # Show bridge capabilities
    print("\n\nBridge score methods:")

    print("\n  SanctionsSignalBridge:")
    print("    - get_signal_score(entity_id, locale, context)")

    print("\n  CorporateSignalBridge:")
    print("    - get_signal_score(entity_id, locale, context)")
    print("    Returns: registration_score, status_score, age_score, lei_score")

    print("\n  DNSSignalBridge:")
    print("    - get_email_auth_score(domain, context)")
    print("    - get_dnssec_score(domain, context)")
    print("    - get_domain_age_score(domain, context)")

    print("\n  NetworkSignalBridge:")
    print("    - get_security_headers_score(domain, context)")
    print("    - get_tls_config_score(domain, context)")
    print("    - get_infrastructure_score(domain, context)")

    print("\n  SecuritySignalBridge:")
    print("    - get_vulnerability_score(entity_id, context)")


def demo_extractor_tiers():
    """Demonstrate extractor tier system."""
    print_header("EXTRACTOR TIER SYSTEM")

    # Count extractors by tier
    tier_counts = {}
    for ext, tier in EXTRACTOR_TIERS.items():
        tier_counts[tier.value] = tier_counts.get(tier.value, 0) + 1

    print("Extractors by tier:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier:15} : {count} extractors")

    print("\nFree tier extractors (sample):")
    free_extractors = [
        ext for ext, tier in EXTRACTOR_TIERS.items()
        if tier == ExtractorTier.FREE
    ]
    for ext in free_extractors[:10]:
        print(f"  - {ext}")
    if len(free_extractors) > 10:
        print(f"  ... and {len(free_extractors) - 10} more")


def demo_routed_functions():
    """Demonstrate routed inference functions."""
    print_header("ROUTED INFERENCE FUNCTIONS")

    print("Available routed inference functions:")
    print("""
  Sanctions & Corporate:
    - sanctions_check_routed     : Multi-source sanctions screening
    - corporate_registry_routed  : Multi-registry company lookup
    - corporate_status_routed    : Company active/dissolved status
    - corporate_age_routed       : Company age/establishment
    - lei_verification_routed    : Legal Entity Identifier check

  DNS:
    - email_auth_routed          : SPF/DKIM/DMARC configuration
    - dnssec_routed              : DNSSEC validation status
    - domain_age_routed          : Domain registration age

  Network:
    - security_headers_routed    : HTTP security headers
    - tls_config_routed          : TLS/SSL configuration
    - infrastructure_routed      : Cloud/CDN/WAF detection

  Security:
    - vulnerability_routed       : CVE exposure check
    - breach_history_routed      : Data breach history
""")

    print("Usage example:")
    print("""
    from signals.inference.functions.routed import (
        sanctions_check_routed,
        corporate_registry_routed,
    )
    from signals.types import InferenceContext

    # Create context with locale
    context = InferenceContext(
        configuration={},
        coverage='general',
        config_name='test',
        entity_locale='UK',
        entity_country='United Kingdom',
        locale_source='submission',
    )

    # Run routed signal
    result = sanctions_check_routed('Test Company Ltd', context)
    print(f"Score: {result.score}")
    print(f"Sources: {result.metadata.get('sources_checked')}")
""")


def run_all_demos():
    """Run all demonstration sections."""
    print("\n" + "=" * 60)
    print("DSI PHASE 15 - HYBRID MODE DEMONSTRATION")
    print("=" * 60)
    print("""
This demo showcases the new routing architecture:

1. Jurisdiction-Aware Routing
   - Routes entities to appropriate regional + global extractors
   - Supports different strategies (locale-only, global-only, locale+global)

2. Locale Detection
   - Automatically detects locale from domain TLD
   - Falls back through priority cascade

3. Routing Cache
   - TTL-based caching at routing level
   - Reduces redundant extractor calls

4. Bridge Aggregators
   - Convert multi-source results to signal scores
   - Handle variance across different source formats

5. Extractor Tiers
   - FREE, PAID_BASIC, PAID_PREMIUM, ENTERPRISE
   - Filter extractors by tier for cost control

6. Routed Inference Functions
   - Drop-in replacements for single-source functions
   - Multi-source aggregation with unified schemas
""")

    demo_jurisdiction_routing()
    demo_locale_detection()
    demo_routing_strategies()
    demo_extractor_tiers()
    demo_routing_cache()
    demo_bridge_aggregators()
    demo_routed_functions()

    print_header("DEMO COMPLETE")
    print("""
Summary:
- Jurisdiction routing selects appropriate extractors based on locale
- Routing strategies control global vs regional extractor selection
- Caching reduces API calls for repeated queries
- Bridge aggregators normalize multi-source results to scores
- Tier system enables cost control for paid extractors
- Routed functions provide multi-source aggregation transparently

The hybrid mode allows gradual migration from stubs to production
extractors as API keys and integrations are added.
""")


if __name__ == "__main__":
    run_all_demos()
