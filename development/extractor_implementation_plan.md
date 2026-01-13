# DSI Extractor Production Implementation Plan

## Executive Summary

This document outlines the plan to convert DSI extractors from stub implementations to production-ready data integrations. Based on analysis of 200+ extractors across 7 coverage types, we've categorized data sources by accessibility, cost, and implementation complexity.

**Key Findings:**
- ~35% of extractors can use FREE public data sources
- ~40% require PAID commercial APIs ($110K-$470K/year estimated)
- ~15% can use web scraping/NLP (infrastructure cost only)
- ~10% require proprietary/restricted access

---

## Phase 1: Free Public Sources (Implement Now)

These extractors can be built immediately using freely available public APIs and databases.

### 1.1 DNS & Network Infrastructure (8 extractors)

| Extractor | Data Source | Implementation |
|-----------|-------------|----------------|
| `EmailAuthExtractor` | DNS TXT records (SPF, DKIM, DMARC) | `dnspython` library - direct DNS queries |
| `DNSSECExtractor` | DNS DNSSEC records | `dnspython` - check DNSKEY, RRSIG records |
| `SecurityTxtExtractor` | `/.well-known/security.txt` | HTTP GET request, RFC 9116 parsing |
| `CloudInfraExtractor` | DNS/IP range analysis | `dnspython` + IP range databases (free) |
| `CDNUsageExtractor` | DNS CNAME analysis | `dnspython` - detect CDN CNAMEs |
| `WAFPresenceExtractor` | HTTP response headers | Direct HTTP requests, header analysis |
| `SecurityHeadersExtractor` | HTTP response headers | Check CSP, HSTS, X-Frame-Options, etc. |
| `TLSConfigExtractor` | TLS handshake | `ssl` library or SSL Labs API (free tier) |

**Implementation Notes:**
- SSL Labs API: Free but rate-limited. Contact Qualys for commercial use permission.
- All DNS-based extractors: No API key needed, use `dnspython`
- HTTP header extractors: Standard requests library

**Estimated Effort:** 2-3 weeks for full implementation

### 1.2 Government Regulatory Databases (15 extractors)

| Extractor | Data Source | Access |
|-----------|-------------|--------|
| `RegulatoryEnforcementExtractor` | Multiple agencies | See below |
| `EPAViolationExtractor` | [EPA ECHO Database](https://echo.epa.gov/) | FREE REST API |
| `OSHAViolationsExtractor` | [OSHA Data](https://www.osha.gov/data) | FREE, downloadable CSV |
| `BSEEIncidentExtractor` | [BSEE Incident Data](https://www.bsee.gov/stats-facts) | FREE downloads |
| `OperatingCertificateExtractor` | FAA Certificate Database | FREE lookup |
| `RampInspectionExtractor` | EASA SAFA Database | PUBLIC access |
| `EUSafetyListExtractor` | EU Air Safety List | FREE download |
| `EnforcementActionExtractor` | OCC/FDIC/Fed databases | FREE FOIA data |
| `PermitStatusExtractor` | State environmental databases | FREE (varies by state) |
| `SanctionsStatusExtractor` | [OFAC SDN List](https://sanctionssearch.ofac.treas.gov/) | FREE API/download |
| `LicenseStatusExtractor` | State licensing boards | FREE (web scraping needed) |
| `CFPBComplaintsExtractor` | [CFPB Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) | FREE REST API |

**SEC EDGAR (Multiple Extractors):**
- `PublicFinancialsExtractor` - 10-K, 10-Q filings
- `LitigationHistoryExtractor` - 8-K disclosures
- `GovernanceRatingExtractor` - Proxy statements (DEF 14A)
- Access: [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation) - FREE

**Estimated Effort:** 3-4 weeks for full implementation

### 1.3 Breach & Incident Databases (5 extractors)

| Extractor | Data Source | Access |
|-----------|-------------|--------|
| `BreachHistoryExtractor` | [HHS Breach Portal](https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf) | FREE - scraping |
| `AviationSafetyDatabaseExtractor` | [Aviation Safety Network](https://aviation-safety.net/) | FREE - scraping |
| `CredentialExposureExtractor` | Have I Been Pwned | FREE (limited) / Paid tiers |
| `IncidentHistoryExtractor` | Domain-specific databases | Varies - mostly FREE |

**HIBP Pricing ([Source](https://haveibeenpwned.com/Subscription)):**
- Personal use: Free
- Pwned 1 (basic): ~$3.25/month (annual)
- Enterprise: Contact for pricing

**Estimated Effort:** 1-2 weeks

### 1.4 Industry & Professional Databases (6 extractors)

| Extractor | Data Source | Access |
|-----------|-------------|--------|
| `PCAOBStandingExtractor` | [PCAOB Firm Database](https://pcaobus.org/registration/firms) | FREE |
| `IOSARegistryExtractor` | IATA IOSA Registry | PUBLIC (registration may be needed) |
| `FlagStateQualityExtractor` | IMO GISIS Database | PUBLIC access |
| `ClassificationSocietyExtractor` | Lloyd's Register, DNV, ABS | PUBLIC registries |
| `IndustryAssociationExtractor` | Association directories | FREE (web scraping) |

**Estimated Effort:** 1-2 weeks

---

## Phase 2: Low-Cost Commercial APIs ($5K-$25K/year)

### 2.1 Network Scanning & Security Intelligence

| Service | Use Case | Pricing | Recommendation |
|---------|----------|---------|----------------|
| **Shodan** | Network exposure, open ports | $49 one-time / $69-$1,099/mo | Start with Freelancer ($69/mo) |
| **Censys** | Internet-wide scanning | Contact for Enterprise | Alternative to Shodan |
| **SSL Labs** | TLS configuration | Free (rate-limited) | Contact Qualys for commercial |

**Shodan Pricing ([Source](https://account.shodan.io/billing)):**
- Membership: $49 one-time
- Freelancer: $69/month
- Small Business: $359/month (includes `vuln` filter)
- Corporate: $1,099/month (includes `tag` filter)
- Enterprise: Contact sales

**Implementation:**
- `NetworkExposureExtractor`
- `CVEExposureExtractor` (use NVD for free, Shodan for enrichment)

**Estimated Annual Cost:** $828 - $13,188

### 2.2 Technology Stack Detection

| Service | Use Case | Pricing | Notes |
|---------|----------|---------|-------|
| **BuiltWith** | Technology detection | $295-$995/mo | API credits vary by plan |
| **Wappalyzer** | Technology detection | Free tier available | Good alternative |

**BuiltWith Pricing ([Source](https://builtwith.com/plans)):**
- Basic: $295/month (2,000 lookups)
- Team: $995/month (includes API credits)

**Implementation:**
- `SoftwareCurrencyExtractor`
- `CloudInfraExtractor` (enrichment)
- `TechnicalContentExtractor`

**Estimated Annual Cost:** $0 (Wappalyzer free) - $11,940 (BuiltWith Team)

### 2.3 Corporate Data

| Service | Use Case | Pricing | Notes |
|---------|----------|---------|-------|
| **OpenCorporates** | Company registry data | Free (open projects) / Paid commercial | Contact for pricing |
| **Companies House API** | UK company data | FREE | UK only |
| **SEC EDGAR** | US public companies | FREE | US only |

**OpenCorporates ([Source](https://opencorporates.com/pricing/)):**
- Free: Open data projects, academics, NGOs, journalists
- Commercial: Contact for pricing

**Implementation:**
- `CorporateRegistryExtractor`
- `PublicFinancialsExtractor` (SEC portion)

**Estimated Annual Cost:** $0 - $10,000 (depending on commercial needs)

---

## Phase 3: Mid-Cost Commercial APIs ($25K-$100K/year)

### 3.1 Security Ratings Platforms

| Service | Use Case | Pricing | Coverage |
|---------|----------|---------|----------|
| **SecurityScorecard** | Cyber security ratings | ~$20K+/year | All cyber extractors |
| **BitSight** | Security ratings | Similar to SSC | Alternative |
| **RiskRecon** | Third-party risk | Contact for pricing | Alternative |

**SecurityScorecard ([Source](https://securityscorecard.com/pricing-packages/)):**
- Free: Limited self-assessment
- Business: Custom pricing
- Enterprise: $20,000+/year

**Can Replace Multiple Extractors:**
- `SecurityRatingExtractor`
- `NetworkExposureExtractor`
- `BreachHistoryExtractor` (partial)
- `ComplianceBadgesExtractor` (partial)

**Implementation Decision:** Consider using SecurityScorecard API to replace 5-10 individual extractors.

**Estimated Annual Cost:** $20,000 - $50,000

### 3.2 ESG Data Providers

| Provider | Data | Pricing | Notes |
|----------|------|---------|-------|
| **MSCI ESG** | ESG ratings | $25K-$100K/year | Industry standard |
| **Sustainalytics** | ESG risk ratings | Similar | Now owned by Morningstar |
| **ISS ESG** | Governance scores | Similar | Strong governance focus |
| **CDP** | Environmental data | Contact | Climate-focused |

**Implementation:**
- `ESGCyberExtractor`
- `ESGRatingExtractor` (D&O)
- `GovernanceRatingExtractor`
- `EnergyESGRatingExtractor`

**Estimated Annual Cost:** $25,000 - $100,000

### 3.3 Financial & Business Intelligence

| Service | Use Case | Pricing | Notes |
|---------|----------|---------|-------|
| **Crunchbase** | Startup/funding data | $29-$49/user/mo (Pro) | Enterprise contact |
| **PitchBook** | Private company data | ~$20K+/year | More comprehensive |
| **D&B (Dun & Bradstreet)** | Business credit/info | Contact for API | Industry standard |

**Crunchbase Pricing:**
- Basic: Free (limited)
- Pro: $29-$49/user/month
- Enterprise API: Contact for pricing

**Implementation:**
- `FinancialRelationshipExtractor`
- `CorporateRegistryExtractor` (enrichment)

**Estimated Annual Cost:** $5,000 - $50,000

---

## Phase 4: Premium APIs ($100K+/year)

### 4.1 Credit Rating Agencies

| Provider | Data | Estimated Cost | Notes |
|----------|------|----------------|-------|
| **S&P Global Ratings** | Credit ratings, outlook | $50K-$200K/year | Enterprise license |
| **Moody's** | Credit ratings | Similar | Competing provider |
| **Fitch Ratings** | Credit ratings | Similar | Third major agency |

**Implementation:**
- `CreditRatingExtractor` (shared across all coverages)

**Estimated Annual Cost:** $50,000 - $200,000

**Alternative:** Use proxy signals (public filings, bond spreads, CDS prices) for ~80% coverage at lower cost.

### 4.2 Specialized Industry Data

| Service | Coverage | Estimated Cost | Notes |
|---------|----------|----------------|-------|
| **OAG** | Flight schedules | $20K-$50K/year | Aerospace |
| **Cirium** | Aviation data | $30K-$100K/year | Comprehensive aviation |
| **Lloyd's List Intelligence** | Marine data | $15K-$50K/year | Shipping |
| **MarineTraffic** | AIS vessel data | $5K-$50K/year | Vessel tracking |
| **IHS Markit** | Energy data | $50K+/year | Energy sector |

**Implementation:**
- `FlightOperationsExtractor` (Aerospace)
- `FleetRegistryExtractor` (Aerospace, Marine)
- `DarkActivityExtractor` (Marine - AIS data)
- `EnergyBenchmarkExtractor` (Energy)

**Estimated Annual Cost:** $70,000 - $250,000 (if all sectors needed)

---

## Phase 5: Web Scraping Infrastructure

For extractors that rely on public website data:

### 5.1 Scraping Targets

| Extractor Type | Target | Technique |
|----------------|--------|-----------|
| `SecurityPageExtractor` | Company security pages | BeautifulSoup + NLP |
| `PrivacyPolicyExtractor` | Privacy policy pages | BeautifulSoup + NLP |
| `SecurityHiringExtractor` | Job boards | API + scraping |
| `CustomerQualityExtractor` | Case study pages | BeautifulSoup |
| `PartnerNetworkExtractor` | Partner pages | BeautifulSoup |
| `BugBountyExtractor` | HackerOne, Bugcrowd | Public APIs |

### 5.2 Infrastructure Needs

| Component | Options | Cost |
|-----------|---------|------|
| Proxy rotation | Bright Data, ScraperAPI | $50-$500/mo |
| Headless browser | Playwright, Puppeteer | Free (infrastructure) |
| NLP processing | spaCy, HuggingFace | Free (compute costs) |
| Storage | PostgreSQL, S3 | ~$100-$500/mo |

**Estimated Annual Cost:** $2,000 - $12,000

### 5.3 Legal Considerations

- Always respect `robots.txt`
- Review Terms of Service
- Rate limit requests (be a good citizen)
- Cache results to minimize requests
- Consider official APIs where available

---

## Implementation Priority Matrix

### Tier 1: Implement Immediately (Week 1-4)
High value, zero/low cost

| Priority | Extractors | Value | Cost |
|----------|------------|-------|------|
| 1 | DNS/Network (8) | Core security signals | $0 |
| 2 | SEC EDGAR (5) | Public company data | $0 |
| 3 | Government Regulatory (15) | Compliance signals | $0 |
| 4 | Security Headers/TLS (3) | Technical security | $0 |

### Tier 2: Quick Wins (Week 5-8)
Moderate value, low cost

| Priority | Extractors | Value | Cost |
|----------|------------|-------|------|
| 5 | Shodan integration (3) | Network exposure | ~$1K/yr |
| 6 | HIBP integration (2) | Breach data | ~$500/yr |
| 7 | Web scraping infra (10) | Website analysis | ~$5K/yr |
| 8 | OpenCorporates (2) | Corporate registry | ~$0-10K/yr |

### Tier 3: Strategic Investments (Month 3-6)
High value, significant cost

| Priority | Extractors | Value | Cost |
|----------|------------|-------|------|
| 9 | SecurityScorecard (5-10) | Replaces many extractors | ~$25K/yr |
| 10 | ESG Provider (4) | ESG/Governance signals | ~$30K/yr |
| 11 | Credit Ratings (1 shared) | Critical for all coverages | ~$75K/yr |

### Tier 4: Sector-Specific (As Needed)
Deploy based on coverage demand

| Priority | Extractors | Coverage | Cost |
|----------|------------|----------|------|
| 12 | Aviation data (5) | Aerospace | ~$50K/yr |
| 13 | Marine/AIS data (5) | Marine | ~$25K/yr |
| 14 | Energy data (5) | Energy | ~$50K/yr |

---

## Cost Summary by Implementation Tier

| Tier | Extractors | Annual Cost | Cumulative |
|------|------------|-------------|------------|
| **Tier 1** | 31 extractors | $0 | $0 |
| **Tier 2** | 17 extractors | ~$15,500 | $15,500 |
| **Tier 3** | 15 extractors | ~$130,000 | $145,500 |
| **Tier 4** | 15 extractors | ~$125,000 | $270,500 |

**Recommended Starting Budget:** $15,000-$50,000/year (Tiers 1-2 + selective Tier 3)

---

## Technical Architecture Recommendations

### 1. Extractor Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 10  # requests per second
    timeout: int = 30
    cache_ttl: int = 3600  # seconds

@dataclass
class ExtractionResult:
    """Result from an extractor."""
    data: dict
    source: str
    confidence: float
    extracted_at: datetime
    cache_hit: bool = False
    error: Optional[str] = None

class ProductionExtractor(ABC):
    """Base class for production extractors."""

    @abstractmethod
    def extract(self, entity_id: str, context: dict) -> ExtractionResult:
        """Extract data for an entity."""
        pass

    @abstractmethod
    def get_data_sources(self) -> list[str]:
        """Return list of data sources used."""
        pass

    @abstractmethod
    def get_cost_tier(self) -> str:
        """Return cost tier: 'free', 'low', 'medium', 'high'."""
        pass
```

### 2. Caching Strategy

```python
# Redis-based caching for API responses
CACHE_TTL = {
    'dns': 3600,           # 1 hour - DNS records
    'tls': 86400,          # 24 hours - TLS config
    'regulatory': 604800,  # 1 week - regulatory data
    'financial': 86400,    # 24 hours - financials
    'ratings': 86400,      # 24 hours - ratings
}
```

### 3. Rate Limiting

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=1)  # 10 calls per second
def call_api(url: str) -> dict:
    """Rate-limited API call."""
    pass
```

### 4. Fallback Strategy

```python
class ExtractorChain:
    """Try multiple data sources in order."""

    def __init__(self, extractors: list[ProductionExtractor]):
        self.extractors = extractors

    def extract(self, entity_id: str, context: dict) -> ExtractionResult:
        for extractor in self.extractors:
            try:
                result = extractor.extract(entity_id, context)
                if result.data and result.confidence > 0.5:
                    return result
            except Exception as e:
                continue
        return ExtractionResult(data={}, source='none', confidence=0)
```

---

## Next Steps

1. **Week 1-2:** Implement Tier 1 free extractors (DNS, SEC EDGAR, regulatory)
2. **Week 3-4:** Set up web scraping infrastructure
3. **Month 2:** Integrate Shodan, HIBP, and OpenCorporates
4. **Month 3:** Evaluate and select ESG provider
5. **Month 4-6:** Negotiate enterprise contracts (SecurityScorecard, Credit Ratings)

---

## Appendix: Data Source Quick Reference

### Free APIs
- SEC EDGAR: https://www.sec.gov/edgar/sec-api-documentation
- EPA ECHO: https://echo.epa.gov/tools/web-services
- OFAC SDN: https://sanctionssearch.ofac.treas.gov/
- CFPB Complaints: https://www.consumerfinance.gov/data-research/consumer-complaints/
- NVD (CVE): https://nvd.nist.gov/developers

### Commercial APIs (Contact for Pricing)
- Shodan: https://developer.shodan.io/
- Censys: https://search.censys.io/api
- SecurityScorecard: https://securityscorecard.com/
- MSCI ESG: https://www.msci.com/esg-ratings
- S&P Global: https://www.spglobal.com/

### Web Scraping Libraries
- BeautifulSoup: HTML parsing
- Playwright/Puppeteer: JavaScript rendering
- Scrapy: Large-scale scraping
- spaCy: NLP analysis
