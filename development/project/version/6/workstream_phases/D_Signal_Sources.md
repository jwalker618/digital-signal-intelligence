# Workstream D — Signal Source Integration

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | C2 (External Secrets for paid sources), C3 (observability for per-extractor spans) |
| Phases | D1–D8 |

---

## Overview

Every source identified in the V6 signal-gap review is wired as a `ProductionExtractor` subclass under `signal_architecture/signals/extractors/production/{category}/`. Each extractor:

- Inherits `ProductionExtractor` (`signal_architecture/signals/extractors/production/base.py`).
- Declares `SOURCE_NAME`, `DEFAULT_TTL_SECONDS`, and `get_cost_tier()` returning one of `free`, `low`, `medium`, `high`.
- Registers in `signal_architecture/signals/extractors/production/factory.py`.
- Has cached results via Redis (TTL from the extractor).
- Has a kill-switch env var `DSI_DISABLE_{EXTRACTOR}=1` for emergency shedding.
- Is covered by a unit test in `tests/unit/test_extractors_{category}.py`.
- Has a free/cached fallback where feasible.

Paid extractors are behind env-var gates so the framework runs end-to-end without them (returning `ExtractorResult(data=None, source='not-licensed', confidence=0)` when disabled — the absence-as-signal principle handles this cleanly).

---

## D1 — Universal Web Footprint

**Directory**: `signal_architecture/signals/extractors/production/web/`

| Extractor | Source | Cost | TTL | Notes |
|-----------|--------|------|-----|-------|
| `GitHubOrgExtractor` | GitHub REST + GraphQL | free (token required) | daily | repo count, stars, security policy presence, dependabot posture, release cadence |
| `WaybackExtractor` | archive.org CDX API | free | weekly | first-seen date, snapshot count, content drift |
| `URLScanExtractor` | urlscan.io | free tier (500/day) | hourly | infrastructure linkages, phishing association |
| `CommonCrawlExtractor` | CCX index + WARC | free | monthly | content-at-scale |
| `TrancoRankExtractor` | tranco-list.eu | free | daily | scale rank |
| `GoogleSafeBrowsingExtractor` | SafeBrowsing API | free | daily | malware / phishing flags |
| `PhishTankExtractor` | phishtank.org | free | daily | abuse history |
| `OpenPhishExtractor` | openphish.com | free feed | daily | abuse feed |
| `CloudflareRadarExtractor` | Cloudflare Radar | free | daily | attack telemetry |
| `GoogleTransparencyExtractor` | Google Transparency Report | free | daily | HTTPS posture, phishing |

**New subdirectory**: `signal_architecture/signals/extractors/production/identity/`

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `HIBPExtractor` | haveibeenpwned.com API | low (Pwned1 tier) | weekly |
| `IntelXExtractor` | intelx.io | free tier + paid | weekly |

**New subdirectory**: `signal_architecture/signals/extractors/production/sentiment/`

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `TrustpilotScraper` | trustpilot.com | free (rate-limited) | daily |
| `BBBScraper` | bbb.org | free (rate-limited) | weekly |
| `GlassdoorScraper` | glassdoor.com | free (rate-limited) | weekly |
| `GoogleReviewsExtractor` | Google Places API | low ($17/1000) | weekly |

**Acceptance for D1**:
- All 16 extractors registered, cached, tested.
- CI matrix exercises each extractor against a golden fixture (no live API calls in unit tests; replayed via `responses` library).
- Kill-switch env vars documented in `.env.example` and `deploy/kubernetes/configmap.yaml`.

---

## D2 — Technical / Infrastructure

**Existing**: `signal_architecture/signals/extractors/production/network/` (extended).
**New subdirectory**: `signal_architecture/signals/extractors/production/stack/`.

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `ShodanExtractor` | shodan.io | low–medium | daily |
| `CensysExtractor` | censys.io | medium | daily |
| `BGPExtractor` | RIPEstat | free | weekly |
| `PeeringDBExtractor` | peeringdb.com | free | weekly |
| `WappalyzerExtractor` | Wappalyzer OSS | free | daily |
| `BuiltWithExtractor` | builtwith.com API | medium | weekly |
| `HTTPArchiveExtractor` | BigQuery public dataset | free (query cost) | monthly |

**Acceptance**:
- `ShodanExtractor` pulls port exposure + CVE summary for a test entity.
- `CensysExtractor` returns a certificate chain and ASN detail.
- `WappalyzerExtractor` returns a deterministic stack fingerprint for a fixture URL.
- `BuiltWithExtractor` is no-op when `BUILTWITH_API_KEY` is absent; `Wappalyzer` is the fallback.

---

## D3 — Litigation & Regulatory Extensions

**Existing**: `regulatory/`, `sanctions/`, `sec/`, `corporate/` (extended).
**New subdirectory**: `signal_architecture/signals/extractors/production/litigation/`.

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `CourtListenerExtractor` | courtlistener.com | free | daily |
| `PACERRSSExtractor` | pacer.gov RSS feeds | free (court-level) | daily |
| `StanfordSCACExtractor` | securities.stanford.edu | free | weekly |
| `SECLitigationReleasesExtractor` | sec.gov/litigation/litreleases.htm | free | daily |
| `FINRABrokerCheckExtractor` | brokercheck.finra.org | free | weekly |
| `SECIAPDExtractor` | adviserinfo.sec.gov | free | weekly |
| `GDPREnforcementTrackerExtractor` | enforcementtracker.com | free | weekly |
| `CMSHospitalCompareExtractor` | data.cms.gov | free | monthly |
| `JointCommissionExtractor` | qualitycheck.org | free | monthly |
| `NPDBPublicExtractor` | npdb.hrsa.gov public summary | free | monthly |
| `PCAOBQSAASVExtractor` | pcaobus.org | free | monthly |
| `OSHAEstablishmentExtractor` | osha.gov/data | free | monthly |
| `FMCSASMSExtractor` | ai.fmcsa.dot.gov | free | weekly |
| `NHTSARecallsExtractor` | nhtsa.gov/recalls | free | daily |
| `CPSCRecallsExtractor` | cpsc.gov/Recalls | free | daily |
| `FDARecallsExtractor` | fda.gov/safety/recalls | free | daily |
| `EUSafetyGateExtractor` | ec.europa.eu/safety-gate | free | daily |
| `USDAFSISRecallsExtractor` | fsis.usda.gov/recalls | free | daily |

**Acceptance**: all 18 extractors live; regression fixtures exercised in CI.

---

## D4 — IP / Innovation

**New subdirectory**: `signal_architecture/signals/extractors/production/ip/`

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `USPTOExtractor` | PatentsView + Peds | free | monthly |
| `EPOOpsExtractor` | EPO OPS | free (rate-limited) | monthly |
| `OpenAlexExtractor` | openalex.org | free | monthly |
| `CrossRefExtractor` | crossref.org | free | monthly |
| `SemanticScholarExtractor` | semanticscholar.org | free | monthly |

**Signals exposed**: `patent_filing_velocity`, `patent_litigation_density`, `research_vitality_index`, `publication_citation_count`, `coauthor_network_depth`.

**Acceptance**: used by PI (A8), TEO (B8), D&O (A4).

---

## D5 — Climate / Environment

**New subdirectory**: `signal_architecture/signals/extractors/production/climate/`
**Existing**: `environment/` (extended).

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `FEMAFloodExtractor` | NFHL (hazards.fema.gov) | free | quarterly |
| `NOAACDOExtractor` | ncdc.noaa.gov | free | daily |
| `USFSFireHazardExtractor` | fs.usda.gov | free | quarterly |
| `USGSSeismicExtractor` | earthquake.usgs.gov | free | monthly |
| `CopernicusSentinelExtractor` | sentinel-hub.com (free tier) | free | weekly |
| `ECMWFERA5Extractor` | cds.climate.copernicus.eu | free | monthly |
| `CDPOpenDataExtractor` | cdp.net | free | quarterly |
| `ENERGYSTARExtractor` | energystar.gov | free | quarterly |
| `TRIExtractor` | epa.gov/toxics-release-inventory | free | quarterly |
| `SuperfundExtractor` | epa.gov/superfund | free | quarterly |
| `NRCInspectionExtractor` | nrc.gov | free | quarterly |

**Acceptance**: used by Property (A2), Energy (A8), Env Liability (B4), Crop (B10).

---

## D6 — Sector Telemetry

**New subdirectories**: `signal_architecture/signals/extractors/production/aviation/`, extensions to `maritime/`, `energy/` (new).

### Aviation
| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `OpenSkyExtractor` | opensky-network.org | free | daily |
| `ICAORegistryExtractor` | icao.int public registries | free | monthly |
| `ASIASExtractor` | asias.faa.gov | free | monthly |

### Maritime (extension)
| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `AISHubExtractor` | aishub.net | low | hourly |
| `MarineCadastreExtractor` | marinecadastre.gov | free | daily |
| `EMSAExtractor` | emsa.europa.eu THETIS | free (with registration) | weekly |
| `ParisMoUExtractor` | parismou.org | free | weekly |
| `TokyoMoUExtractor` | tokyo-mou.org | free | weekly |

### Energy
| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `PHMSAExtractor` | phmsa.dot.gov | free | monthly |
| `BSEEDetailExtractor` | bsee.gov (deeper use) | free | monthly |
| `NERCVioExtractor` | nerc.com | free | monthly |

**Acceptance**: used by Aerospace (A6), Marine (A7), Energy (A8), Env Liability (B4).

---

## D7 — Hiring / Behavioural Derivatives

**New subdirectory**: `signal_architecture/signals/extractors/production/hiring/`

| Extractor | Source | Cost | TTL |
|-----------|--------|------|-----|
| `GreenhouseScraper` | boards.greenhouse.io/<company> | free | daily |
| `LeverScraper` | jobs.lever.co/<company> | free | daily |
| `AshbyScraper` | jobs.ashbyhq.com/<company> | free | daily |
| `GoogleJobsExtractor` | jobs.google.com | free (SerpAPI or scraping) | daily |

**Velocity derivative**: rolling 90-day delta in active job postings, feature-extracted as `hiring_velocity_score` and `hiring_velocity_vs_peers`. This feeds directly into `world_engine/drift/detector.py` as the **Velocity** derivative referenced in the vision paper.

**Implementation**:
- Add `world_engine/derivatives/velocity.py` computing rolling delta per entity.
- Wire output to `world_engine/drift/detector.py` as a new detection mode (`VelocityDetection`).
- Expose signal `hiring_velocity` across all coverages where applicable (Cyber, PI, TEO, D&O, FI, Energy, Aero, Marine, Medprof).

**Acceptance**:
- Nightly scan computes velocity for every monitored entity.
- `world_engine/drift/detector.py` produces `VelocityAlert` when an entity's delta exceeds the configured threshold.
- Velocity visible in the evidence dashboard (E8).

---

## D8 — Cost-Aware Signal Broker

**File**: `signal_architecture/signals/routing/source_router.py`

**Problem**: multiple extractors can satisfy the same signal (e.g., `technology_stack` ← Wappalyzer OR BuiltWith). The broker should choose the cheapest source that satisfies the config's confidence floor.

**Design**:
```python
class SignalBrokerV2:
    def __init__(self, extractor_registry, config_registry):
        self.extractors = extractor_registry
        self.configs = config_registry

    def extract(self, signal_id, entity_id, min_confidence=0.6):
        candidates = self.extractors.for_signal(signal_id)
        # sort by cost tier: free -> low -> medium -> high
        candidates.sort(key=lambda e: e.cost_tier_rank())
        for extractor in candidates:
            if extractor.is_disabled():        # kill-switch
                continue
            try:
                result = extractor.extract(entity_id, context)
                if result.confidence >= min_confidence:
                    return result
            except ExtractorError:
                continue
        return ExtractorResult.neutral_absence(signal_id)
```

**Cross-walk updates**: `signal_architecture/signals/cross_walk/by_coverage.json` extended so every signal ID lists all capable extractors in descending preference.

**Kill-switches**: every paid extractor checks `DSI_DISABLE_{NAME}` and, where present, returns `is_disabled=True`.

**Cost telemetry**: every successful extraction emits a `dsi_extractor_cost_usd` counter labeled by extractor + cost tier. Grafana dashboard (`extractors.json` from C3) shows monthly cost projection.

**Acceptance**:
- Toggling `DSI_DISABLE_BUILTWITH=1` causes all stack-detection traffic to route to Wappalyzer without ops intervention.
- Monthly extractor-cost projection in Grafana matches actual billing within 10%.
- A config can declare a `preferred_source` hint that the broker honours when it doesn't materially increase cost.

---

## Acceptance for Workstream D

- `signal_architecture/signals/extractors/production/` contains the new subdirectories (`web/`, `identity/`, `sentiment/`, `stack/`, `litigation/`, `ip/`, `climate/`, `aviation/`, `hiring/`) plus extensions to existing dirs, with a total of ≥100 production extractors.
- Every new extractor has a unit test in `tests/unit/test_extractors_{category}.py`.
- `.env.example` lists every new env var (API key and kill-switch).
- `deploy/kubernetes/configmap.yaml` lists every kill-switch default.
- The cost-aware broker is live and monitored.
- `world_engine/derivatives/velocity.py` produces nightly deltas fed into drift detection.
