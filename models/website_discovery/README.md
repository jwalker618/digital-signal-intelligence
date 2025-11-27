# Website Discovery Module

## Overview

The `website_discovery` module solves the critical problem of identifying the correct corporate website for an organisation. This is a foundational component of DSI, enabling automated signal collection by first resolving which website to analyse.

## Key Capabilities

### 1. Multi-Method Discovery
- **Direct domain validation** - When domain hints are provided
- **Name-based generation** - Creates candidate domains from company names
- **Corporate registry lookup** - Companies House, SEC EDGAR, OpenCorporates
- **Search engine discovery** - Google/Bing search for official sites
- **DNS enumeration** - TLD variations and regional variants

### 2. Corporate Structure Resolution
- Identifies parent/subsidiary relationships
- Handles brands within larger companies
- Maps holding company structures
- Example: "MS Amlin" → MS&AD Insurance Group Holdings

### 3. Confidence Scoring
- **HIGH** (90%+): Multiple signals align, verified domain
- **MEDIUM** (70-89%): Some ambiguity, likely correct
- **LOW** (50-69%): Significant uncertainty
- **UNVERIFIED** (<50%): Requires manual verification

### 4. Red Flag Detection
- Parked/inactive domains
- Suspicious domain patterns
- Domain age inconsistencies
- SSL/registration mismatches

## Usage

### Basic Discovery
```python
from website_discovery import WebsiteDiscoveryEngine

engine = WebsiteDiscoveryEngine()
result = engine.discover("MS Amlin")

print(f"Domain: {result.primary_website.domain}")
print(f"Confidence: {result.confidence.value}")
print(f"Manual Review Required: {result.requires_manual_review}")
```

### Discovery with Hints
```python
result = engine.discover(
    company_name="Petrobras",
    domain_hint="petrobras.com.br",
    country_hint="Brazil",
    industry_hint="energy"
)
```

### Batch Discovery
```python
from website_discovery import BatchWebsiteDiscovery

batch = BatchWebsiteDiscovery()
results = batch.discover_batch([
    {"name": "MS Amlin", "country": "UK", "industry": "insurance"},
    {"name": "Petrobras", "domain_hint": "petrobras.com.br"},
    {"name": "Boeing", "country": "US"}
])

for name, result in results.items():
    print(f"{name}: {result.primary_website.domain} ({result.confidence.value})")
```

### Domain Validation
```python
from website_discovery import validate_corporate_domain

is_valid, confidence, issues = validate_corporate_domain(
    domain="petrobras.com.br",
    expected_company="Petrobras"
)
```

## Data Structures

### DiscoveryResult
```python
@dataclass
class DiscoveryResult:
    input_name: str                                   # Original search name
    primary_website: WebsiteCandidate                 # Best match
    confidence: ConfidenceLevel                       # Overall confidence
    all_candidates: List[WebsiteCandidate]            # All discovered candidates
    company_identity: CompanyIdentity                 # Resolved corporate identity
    related_websites: Dict[str, WebsiteCandidate]     # Parent, subsidiaries, etc.
    requires_manual_review: bool                      # Flag for human review
    manual_review_reasons: List[str]                  # Why review needed
```

### WebsiteCandidate
```python
@dataclass
class WebsiteCandidate:
    url: str                                  # Full URL
    domain: str                               # Domain only
    website_type: WebsiteType                 # PRIMARY_CORPORATE, SUBSIDIARY, etc.
    discovery_method: DiscoveryMethod         # How it was found
    confidence_score: float                   # 0-100 score
    evidence: List[str]                       # Supporting evidence
    red_flags: List[str]                      # Concerns identified
```

## Configuration

```python
engine = WebsiteDiscoveryEngine(config={
    'search_api_key': 'your_key',
    'whois_service': 'https://whois.api.com',
    'timeout': 30,
    'registry_apis': {
        'uk': 'https://api.company-information.service.gov.uk',
        'us': 'https://www.sec.gov/cgi-bin/browse-edgar'
    }
})
```

## Integration with Signal Collection

The website_discovery module is designed to integrate with signal_collection:

```python
from website_discovery import WebsiteDiscoveryEngine
from signal_collection import SignalCollectionEngine

# Discover website first
discovery = WebsiteDiscoveryEngine()
website_result = discovery.discover("Target Company")

# Use discovered domain for signal collection
signals = SignalCollectionEngine()
signal_result = signals.collect(
    entity_name="Target Company",
    domain_hint=website_result.primary_website.domain
)
```

## Known Limitations

1. **Private companies**: Limited public information may result in lower confidence
2. **New companies**: Recent formations may not appear in registries
3. **Rebranded companies**: May have multiple valid domains
4. **Regional variants**: May resolve different regional sites

## Future Enhancements

- [ ] Integration with actual APIs (Companies House, SEC, etc.)
- [ ] Machine learning for logo/content matching
- [ ] Real-time domain monitoring
- [ ] Historical domain tracking
- [ ] Brand/trademark verification

