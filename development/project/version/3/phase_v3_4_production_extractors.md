# Phase V3-4: Production Signal Extractors

**Status:** Not Started
**Priority:** Medium
**Prerequisites:** V3-1 (Test Recovery)

## Context

Signal extraction currently uses stub extractors that return hardcoded/random scores. Production extractors need to call real APIs and parse real data sources to generate meaningful signal scores.

The extractor factory supports three modes: `stub` (default), `production`, and `hybrid` (production with stub fallback), controlled by `FEATURE_USE_STUBS` environment variable.

## Objective

Implement production extractors for the highest-value signals, starting with those that are externally observable (DIRECT_OBSERVABLE proxy tier) and have available API sources.

## Priority Signals

### Tier 1: DIRECT_OBSERVABLE (free/low-cost)
- `security_headers` — HTTP response header analysis
- `tls_configuration` — SSL/TLS certificate and protocol analysis
- `email_authentication` — SPF, DKIM, DMARC record checks
- `dns_security` — DNSSEC, DNS record analysis
- `ssl_certificate` — Certificate transparency log queries

### Tier 2: DIRECT_OBSERVABLE (paid APIs)
- `breach_history` — HaveIBeenPwned API, breach databases
- `vulnerability_management` — Shodan, Censys exposure data
- `regulatory_filings` — SEC EDGAR, Companies House APIs

### Tier 3: INFERRED_PROXY
- `website_quality` — Lighthouse/PageSpeed analysis
- `social_presence` — LinkedIn, Twitter API analysis
- `credit_rating` — D&B, Experian commercial APIs

## Tasks

1. Implement Tier 1 extractors (free API sources)
2. Integrate paid API extractors with credential management
3. Add extraction caching (TTL from metadata registry)
4. Production smoke tests for each extractor
5. Update extractor factory registration

## Key Files

- `signal_architecture/signals/extractors/` — Extractor implementations
- `infrastructure/integrations/` — API client wrappers
- See also: `development/extractor_implementation_plan.md`

## Success Criteria

- 5+ production extractors returning real data
- Extraction caching respects signal TTL
- Hybrid mode works: production where available, stub fallback
- < 10 second extraction time per signal
