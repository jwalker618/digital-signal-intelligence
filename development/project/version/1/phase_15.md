# Phase 15: Production Extractors & Signal Routing

## Purpose
Provide a robust library of production‑grade extractors and a routing module capable of selecting the optimal extractor set based on jurisdiction, availability, and tier.

## Key Deliverables
- 50 production extractors
- Routing module
- Routed inference functions
- Multi‑source aggregation
- TTL‑based routing cache

## Implementation Summary
This phase introduces a scalable, jurisdiction‑aware routing system that selects extractors dynamically. It also includes 50 production‑ready extractors and 13 routed inference functions.

## Detailed Plan

Implement production extractors that connect to real data sources with jurisdiction-aware routing for global coverage.

> **Master Implementation Document**: See `development/extractor_implementation_plan.md` for detailed API pricing, cost estimates, implementation timeline, and technical architecture recommendations.

### 15.1 Production Extractor Architecture

Production extractors replace stub extractors with real API connections:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL ROUTING MODULE                        │
│                                                                 │
│  ┌────────────────┐    ┌────────────────┐    ┌───────────────┐  │
│  │JURISDICTION    │ →  │MULTI-SOURCE    │ →  │UNIFIED        │  │
│  │ROUTER          │    │AGGREGATOR      │    │SCHEMA         │  │
│  │                │    │                │    │               │  │
│  │Maps locale →   │    │Parallel calls  │    │Normalized     │  │
│  │extractors      │    │consolidate     │    │output format  │  │
│  └────────────────┘    └────────────────┘    └───────────────┘  │
│                                                                 │
│  Routing Strategies:                                            │
│  - LOCALE_PLUS_GLOBAL: Region-specific + global (recommended)   │
│  - LOCALE_ONLY: Only regional sources                           │
│  - GLOBAL_ONLY: Only global sources                             │
│  - PRIMARY_ONLY: Single best source (fastest)                   │
│  - ALL: All available sources                                   │
│                                                                 │
│  Extractor Tiers:                                               │
│  - FREE: No API keys required (50 extractors implemented)       │
│  - PAID_BASIC: Low-cost APIs (Shodan, VirusTotal)               │
│  - PAID_PREMIUM: Commercial APIs (D&B, Experian, Refinitiv)     │
│  - ENTERPRISE: Premium sources (Bloomberg, FactSet)             │
└─────────────────────────────────────────────────────────────────┘
```

### 15.2 Free Production Extractors (50 Total)

| Category | Count | Extractors | Coverage |
|-|-|-||
| DNS | 4 | email_auth, dnssec, dns_records, whois_rdap | Global |
| HTTP | 2 | security_headers, security_txt | Global |
| Network | 4 | cloud_infra, cdn_usage, waf_presence, tls_config | Global |
| Securities | 5 | sec_filings, sec_financials, sec_litigation, sec_governance, sedar_canada | US, Canada |
| Regulatory | 9 | ofac_sanctions, epa_echo, cfpb_complaints, osha_violations, faa_certificate, eu_safety_list, fdic_enforcement, bsee_incidents, uk_fca_register | US, UK, EU |
| Sanctions | 10 | opensanctions, uk_ofsi, eu_sanctions, worldbank_debarred, interpol_red_notices, fbi_most_wanted, adb_sanctions, idb_sanctions, ebrd_ineligible, afdb_sanctions | Global |
| Security | 2 | nvd_cve, hhs_breach | Global, US |
| Industry | 2 | pcaob, aviation_safety | Global |
| Corporate | 5 | companies_house, opencorporates, australia_abn, india_mca, gleif_lei | UK, AU, IN, Global |
| Environment | 2 | eea_environment, canada_npri | EU, Canada |
| Maritime | 2 | imo_gisis, iosa_registry | Global |

### 15.3 Routing Module Components

```python
# Usage example
from technical_pricing.signals.routing import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    SanctionsAggregator,
)

# Get extractors for UK sanctions check
router = JurisdictionRouter()
extractors = router.get_extractors(
    signal_type='sanctions',
    locale='UK',
    strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
    max_tier=ExtractorTier.FREE,
)
# Returns: ['uk_ofsi', 'opensanctions', 'interpol_red_notices', ...]

# Full multi-source aggregation
aggregator = SanctionsAggregator()
result = aggregator.aggregate(
    entity_id='Acme Corporation',
    signal_type='sanctions',
    locale='UK'
)
print(f"Risk: {result.result.risk_level}")  # CLEAR/LOW/MEDIUM/HIGH/CRITICAL
print(f"Matches: {result.result.total_matches}")
print(f"Sources: {result.result.sources_checked}")
```

### 15.4 Unified Output Schemas

Each signal type has a standardized output schema regardless of data source:

- **SanctionsResult**: risk_level, total_matches, matches[], confirmed_sanctioned
- **CorporateResult**: records_found, primary_record, lei, any_active
- **RegulatoryResult**: total_violations, open_violations, risk_level
- **DomainResult**: domain_age_days, expires_soon, privacy_protected

### 15.5 Signal Framework Integration (Pending)

Integration points to connect routing to existing inference layer:

1. **InferenceContext.entity_locale** - Populate from discovery/submission
2. **Bridge Aggregators** - Convert unified schemas → signal scores
3. **Routed Inference Functions** - Use router instead of hardcoded extractors

```python
# Pending: Bridge aggregator example
class SanctionsSignalAggregator(ProductionAggregator):
    """Converts SanctionsResult → signal score 0-100"""

    RISK_TO_SCORE = {
        RiskLevel.CLEAR: 95,
        RiskLevel.LOW: 75,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 25,
        RiskLevel.CRITICAL: 5,
    }

    def aggregate(self, results, locale, entity_id):
        agg = SanctionsAggregator()
        multi_result = agg.aggregate(entity_id, 'sanctions', locale)
        score = self.RISK_TO_SCORE[multi_result.result.risk_level]
        return AggregatorResult(success=True, data={'score': score})
```

### 15.6 Implementation Tasks

| Task | File | Status |
|-|-|-|
| DNS extractors (4) | `production/dns/` | ✅ Complete |
| HTTP extractors (2) | `production/http/` | ✅ Complete |
| Network extractors (4) | `production/network/` | ✅ Complete |
| SEC extractors (5) | `production/sec/` | ✅ Complete |
| Regulatory extractors (9) | `production/regulatory/` | ✅ Complete |
| Sanctions extractors (10) | `production/sanctions/` | ✅ Complete |
| Security extractors (2) | `production/security/` | ✅ Complete |
| Industry extractors (2) | `production/industry/` | ✅ Complete |
| Corporate extractors (5) | `production/corporate/` | ✅ Complete |
| Environment extractors (2) | `production/environment/` | ✅ Complete |
| Maritime extractors (2) | `production/maritime/` | ✅ Complete |
| JurisdictionRouter | `routing/router.py` | ✅ Complete |
| Unified schemas | `routing/schemas.py` | ✅ Complete |
| MultiSourceAggregator | `routing/multi_source.py` | ✅ Complete |
| SanctionsAggregator | `routing/sanctions_aggregator.py` | ✅ Complete |
| CorporateAggregator | `routing/corporate_aggregator.py` | ✅ Complete |
| ExtractorTier system | `routing/router.py` | ✅ Complete |
| Paid extractor mappings | `routing/router.py` | ✅ Complete |
| InferenceContext.locale | `signals/types.py` | ✅ Complete |
| Bridge aggregators | `aggregators/routing_bridges.py` | ✅ Complete |
| Routed inference functions | `inference/functions/routed/` | ✅ Complete |
| Routing-level caching | `routing/multi_source.py` | ✅ Complete |
| Unit tests for routing | `tests/unit/test_routing.py` | ✅ Complete |
| Hybrid mode demo | `examples/run_hybrid.py` | ✅ Complete |
| Paid extractors (Shodan, etc.) | `production/paid/` | 🔲 Pending |

### 15.7 Phase 15 Integration Layer (Complete)

The routing module is now fully integrated with the signal framework:

#### 15.7.1 InferenceContext Locale Fields
```python
# technical_pricing/signals/types.py
@dataclass
class InferenceContext:
    # ... existing fields ...
    entity_locale: Optional[str] = None      # ISO country code (UK, US, DE)
    entity_country: Optional[str] = None     # Full country name
    locale_source: Optional[str] = None      # 'submission', 'discovery', 'domain_tld'
```

#### 15.7.2 Bridge Aggregators
```python
# technical_pricing/signals/aggregators/routing_bridges.py
class SanctionsSignalBridge(RoutingBridge):
    """Converts SanctionsResult → signal score (0-100)"""
    RISK_TO_SCORE = {CLEAR: 95, LOW: 75, MEDIUM: 50, HIGH: 25, CRITICAL: 5}

class CorporateSignalBridge(RoutingBridge):
    """Multi-score output: registration_score, status_score, age_score, lei_score"""

class DNSSignalBridge(RoutingBridge):
    """Methods: get_email_auth_score, get_dnssec_score, get_domain_age_score"""

class NetworkSignalBridge(RoutingBridge):
    """Methods: get_security_headers_score, get_tls_config_score, get_infrastructure_score"""

class SecuritySignalBridge(RoutingBridge):
    """Method: get_vulnerability_score"""
```

#### 15.7.3 Routed Inference Functions (13 Total)
```python
# technical_pricing/signals/inference/functions/routed/signals.py

# Sanctions & Corporate (5)
sanctions_check_routed         # Multi-source sanctions screening
corporate_registry_routed      # Multi-registry company lookup
corporate_status_routed        # Company active/dissolved status
corporate_age_routed           # Company establishment age
lei_verification_routed        # Legal Entity Identifier check

# DNS (3)
email_auth_routed              # SPF/DKIM/DMARC configuration
dnssec_routed                  # DNSSEC validation status
domain_age_routed              # Domain registration age

# Network (3)
security_headers_routed        # HTTP security headers
tls_config_routed              # TLS/SSL configuration
infrastructure_routed          # Cloud/CDN/WAF detection

# Security (2)
vulnerability_routed           # CVE exposure check
breach_history_routed          # Data breach history
```

#### 15.7.4 Routing-Level Cache
```python
# technical_pricing/signals/routing/multi_source.py
class RoutingCache:
    """Thread-safe TTL cache for extraction results"""
    def get(extractor_name, entity_id) -> Optional[CachedResult]
    def set(extractor_name, entity_id, data, ttl_seconds=300)
    def invalidate(extractor_name=None, entity_id=None) -> int
    def get_stats() -> Dict[str, Any]  # hits, misses, hit_rate

# Global cache singleton
get_routing_cache() -> RoutingCache
set_routing_cache(cache)  # For testing
```

#### 15.7.5 Usage Example
```python
from technical_pricing.signals.inference.functions.routed import (
    sanctions_check_routed,
    corporate_registry_routed,
    register_all,
)
from technical_pricing.signals.types import InferenceContext

# Register all routed functions
register_all()

# Create context with locale
context = InferenceContext(
    configuration={},
    coverage='general',
    config_name='test',
    entity_locale='UK',
    entity_country='United Kingdom',
    locale_source='submission',
)

# Run multi-source sanctions check
result = sanctions_check_routed('Test Company Ltd', context)
print(f"Score: {result.score}")           # 95 = clear, 5 = sanctioned
print(f"Risk: {result.raw_data.get('risk_level')}")
print(f"Sources: {result.metadata.get('sources_checked')}")
```

#### 15.7.6 Hybrid Mode Demo
```bash
# Run the Phase 15 demo
python examples/run_hybrid.py
```

Demonstrates:
- Jurisdiction-aware routing (UK, US, AU, etc.)
- Locale detection from domain TLD
- Routing strategies (LOCALE_ONLY, GLOBAL_ONLY, LOCALE_PLUS_GLOBAL)
- Extractor tier filtering (FREE, PAID_BASIC, PAID_PREMIUM)
- Routing cache with TTL expiration
- Bridge aggregators for all signal types
