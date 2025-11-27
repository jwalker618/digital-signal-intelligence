# Signal Collection Module

## Overview

The `signal_collection` module is the core DSI engine for extracting, analysing, and scoring risk signals from external sources. It transforms observable data into normalised scores that drive pricing decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SignalCollectionEngine                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Website   │  │    DNS      │  │    Third-Party APIs     │ │
│  │  Discovery  │  │  Records    │  │  (Shodan, LinkedIn...)  │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                      │               │
│         ▼                ▼                      ▼               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Signal Collectors                        ││
│  │  WebsiteContent | DNS | SSL | Shodan | LinkedIn | News     ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Scoring Engine                           ││
│  │  Binary | Linear | Logarithmic | Threshold | Percentile    ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Signal Aggregator                        ││
│  │  Group Scores → Overall Score → Tier Assignment            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Signal Taxonomy

### Type 1: Network Authority
- Customer quality
- Partner network
- Security vendor relationships
- Industry body membership
- Certification authority

### Type 2: Technical Infrastructure
- TLS/SSL configuration
- Security headers (HSTS, CSP, etc.)
- Email authentication (SPF, DKIM, DMARC)
- DNSSEC implementation
- Network exposure

### Type 3: Asset Telemetry
- Third-party security ratings
- Dark web monitoring
- Vulnerability assessments

### Type 4: Structured Data
- Industry benchmarks
- Credit ratings
- ESG scores

### Type 5: Corporate Footprint
- Security page presence
- Privacy policy quality
- Bug bounty programs
- Security hiring activity
- Security leadership visibility

### Type 6: Public Records
- Breach history
- Regulatory actions
- Litigation history
- Credential exposure

### Type 7: Direct Inquiry
- Security questionnaire responses
- Attestations (optional, not used in auto-assessment)

## Model-Specific Configurations

### Cyber Insurance
```python
type_weights = {
    TYPE_1_NETWORK_AUTHORITY: 0.15,
    TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.25,  # Highest
    TYPE_3_ASSET_TELEMETRY: 0.15,
    TYPE_4_STRUCTURED_DATA: 0.10,
    TYPE_5_CORPORATE_FOOTPRINT: 0.20,
    TYPE_6_PUBLIC_RECORDS: 0.15,
}
```

### Financial Institutions
```python
type_weights = {
    TYPE_1_NETWORK_AUTHORITY: 0.20,  # Higher
    TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.15,
    TYPE_3_ASSET_TELEMETRY: 0.15,
    TYPE_4_STRUCTURED_DATA: 0.20,  # Higher for regulatory
    TYPE_5_CORPORATE_FOOTPRINT: 0.15,
    TYPE_6_PUBLIC_RECORDS: 0.15,
}
```

### Energy Sector
```python
type_weights = {
    TYPE_1_NETWORK_AUTHORITY: 0.15,
    TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.20,  # OT/IT important
    TYPE_3_ASSET_TELEMETRY: 0.15,
    TYPE_4_STRUCTURED_DATA: 0.15,
    TYPE_5_CORPORATE_FOOTPRINT: 0.20,
    TYPE_6_PUBLIC_RECORDS: 0.15,
}
```

## Usage

### Basic Collection
```python
from signal_collection import SignalCollectionEngine, ModelType

engine = SignalCollectionEngine(model_type=ModelType.CYBER)
result = engine.collect(
    entity_name="Target Company",
    domain_hint="targetcompany.com"
)

print(f"Score: {result.overall_score}/1000")
print(f"Tier: {result.tier}")
```

### Model-Specific Engines
```python
from signal_collection import CyberSignalEngine, EnergySignalEngine

# Cyber-specific collection
cyber_engine = CyberSignalEngine()
cyber_result = cyber_engine.collect("Petrobras")

# Energy-specific collection
energy_engine = EnergySignalEngine()
energy_result = energy_engine.collect(
    "Petrobras",
    domain_hint="petrobras.com.br",
    industry_hint="energy"
)
```

### Factory Pattern
```python
from signal_collection import create_signal_engine, ModelType

engine = create_signal_engine(ModelType.FINANCIAL_INSTITUTIONS)
result = engine.collect("Bank of Example")
```

### Batch Collection
```python
results = engine.collect_batch([
    {"name": "Company A", "domain": "companya.com"},
    {"name": "Company B", "country": "UK"},
    {"name": "Company C", "industry": "healthcare"}
])
```

### Export Results
```python
# Summary format
summary = engine.export_result(result, 'summary')

# Full detail
detail = engine.export_result(result, 'dict')

# JSON string
json_output = engine.export_result(result, 'json')
```

## Scoring Methods

### Binary
Yes/No signals → 0 or 100
```python
# Example: Security.txt present?
score = 100 if present else 0
```

### Linear
Continuous values mapped to 0-100
```python
# Example: SSL Labs score
score = (raw_value - min) / (max - min) * 100
```

### Logarithmic
Large ranges compressed logarithmically
```python
# Example: Credential exposures (more = worse)
score = 100 - min(100, log10(count + 1) * 25)
```

### Threshold
Step function with defined breakpoints
```python
# Example: Breach history
thresholds = [
    (0, 100, "No breaches"),
    (1, 60, "Minor breach >3yr"),
    (2, 40, "Significant breach >3yr"),
    (3, 20, "Recent breach"),
    (4, 0, "Multiple recent")
]
```

### Percentile
Ranking against benchmark dataset
```python
# Example: Security score vs industry
percentile = rank_in_benchmark(raw_value, industry_benchmarks)
```

## Red Flags and Green Flags

### Red Flags (Automatic Risk Elevation)
- Breach history score < 40
- Email authentication score < 20
- Network exposure score < 25
- TLS configuration score < 30

### Green Flags (Positive Indicators)
- Security.txt present
- Bug bounty program active
- Strong certification (SOC 2, ISO 27001)
- Visible security leadership

## Tier Classification

| Tier | Score Range | Risk Level | Recommendation |
|------|-------------|------------|----------------|
| 1 | 800-1000 | Preferred | Auto-approve, possible discount |
| 2 | 650-799 | Standard | Auto-approve at standard pricing |
| 3 | 500-649 | Elevated | Manual review, +15-30% loading |
| 4 | 350-499 | High Risk | Manual review required, +30-60% |
| 5 | 0-349 | Critical | Decline or special terms only |

## Integration Example

```python
from website_discovery import WebsiteDiscoveryEngine
from signal_collection import create_signal_engine, ModelType

def assess_company(company_name, model_type=ModelType.CYBER):
    # Step 1: Discover corporate website
    discovery_engine = WebsiteDiscoveryEngine()
    discovery = discovery_engine.discover(company_name)
    
    if discovery.requires_manual_review:
        print(f"Warning: Website discovery needs review")
    
    # Step 2: Collect signals
    signal_engine = create_signal_engine(model_type)
    result = signal_engine.collect(
        entity_name=company_name,
        domain_hint=discovery.primary_website.domain if discovery.primary_website else None
    )
    
    # Step 3: Return assessment
    return {
        'company': company_name,
        'domain': result.entity_domain,
        'score': result.overall_score,
        'tier': result.tier,
        'recommendation': get_recommendation(result.tier)
    }

def get_recommendation(tier):
    recommendations = {
        1: "Auto-approve at preferred rates",
        2: "Auto-approve at standard rates",
        3: "Manual underwriter review recommended",
        4: "Senior underwriter review required",
        5: "Decline or refer to specialist"
    }
    return recommendations.get(tier, "Unknown")
```

## Custom Collectors

Extend the module with custom collectors:

```python
from signal_collection import SignalCollector, SignalSource, RawSignal

class CustomAPICollector(SignalCollector):
    def get_source_type(self):
        return SignalSource.API_ENDPOINT
    
    def collect(self, target, config):
        # Your custom collection logic
        response = call_custom_api(target)
        
        return [RawSignal(
            signal_id="custom_signal",
            signal_name="Custom API Signal",
            signal_type=SignalType.TYPE_3_ASSET_TELEMETRY,
            source=SignalSource.API_ENDPOINT,
            raw_value=response,
            quality=SignalQuality.HIGH
        )]

# Add to engine
engine = SignalCollectionEngine()
engine.collectors['custom'] = CustomAPICollector()
```

## Future Enhancements

- [ ] Real-time API integrations (SecurityScorecard, BitSight)
- [ ] Machine learning signal weighting
- [ ] Historical signal trending
- [ ] Peer group benchmarking
- [ ] Continuous monitoring mode
- [ ] Alert system for signal changes

