# DSI Version 6: Master Build Sequence

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | April 2026 |
| Classification | Master Execution Plan |

---

## Purpose

Single authoritative document for ordering V6 workstream phases so every file is touched once, in the right order. Applies the V5 sequencing principles verbatim.

## Sequencing Principles

1. **Schema before logic** — alembic migrations land first in each quarter.
2. **Platform before coverage** — E2 (config health gate), C7 (config-diff CI job), C4 (seed consolidation), E5 (golden entities) gate the coverage work so maturation and expansion cannot silently regress pricing.
3. **Cheapest sources first** — D1 and D3 (free web + regulatory extensions) precede D2/D5/D6 (paid/sector) so signals are available when coverage work needs them.
4. **No file touched twice** — where A and B both need to touch `infrastructure/builder/signal_library.py`, A goes first and B extends.
5. **Backend before frontend** — UI wiring of drift referrals (E6) and evidence dashboard (E8) is last, after their backends are stable.
6. **Seed is the final pre-release gate** — C4 runs after all coverages are mature and all extractors are registered.

---

## Quarter-by-Quarter Sequence

### Q1 — Platform & Weakest Coverages

| Order | Phase | Deliverable |
|-------|-------|-------------|
| 1 | **E2** Config Health Gate | CI job blocks PRs that fail `calibrate` or `assess_config_compliance`. |
| 2 | **C7** Config-Diff CI Job | Rendered `logic.md` diff posted on every PR. |
| 3 | **E5** Golden-Entity Registry | 10 golden entities × 10 existing coverages committed as fixtures; regression test added. |
| 4 | **C1** CI Deploy Wiring | Echo stubs replaced with real `kubectl set image`; canary via Argo Rollouts; rollback verification. |
| 5 | **C2** External Secrets Operator | SecretStore + ExternalSecret per env; kustomize overlays. |
| 6 | **C3** Observability | OpenTelemetry instrumentation; per-extractor spans; four gold-signal SLOs. |
| 7 | **D1** Universal Web Footprint Sources | GitHub, Wayback, urlscan, CommonCrawl, Tranco, Safe Browsing, PhishTank, OpenPhish, Cloudflare Radar, Google Transparency, HIBP, IntelX, Trustpilot, BBB, Glassdoor, Google Reviews. |
| 8 | **D3** Litigation / Regulatory Extensions | CourtListener, PACER, Stanford SCAC, SEC Lit Releases, FINRA, IAPD, GDPR ET, CMS, Joint Commission, NPDB, PCAOB QSA/ASV, OSHA establishment, FMCSA, NHTSA, CPSC, FDA, EU Safety Gate, USDA FSIS. |
| 9 | **A1** FPR Maturation | Split into trade credit / political risk / surety / K&R / SME; 22+ signals; 70+ inf fns. |
| 10 | **A2** Property Maturation | CAT-exposed / high-value / builders' risk / habitational; 22+ signals; 70+ inf fns. |
| 11 | **A3** Casualty Maturation | GL / WC / auto / env / umbrella / SME enriched; 26+ signals; 80+ inf fns. |
| 12 | **C4** Seed Consolidation (interim) | `seed/` package bootstrapped with bench + v5 + synthetic moved; old scripts deprecated (still present). |

### Q2 — Finishing Existing Coverages & First New Coverages

| Order | Phase | Deliverable |
|-------|-------|-------------|
| 13 | **D2** Technical / Infrastructure Sources | Shodan, Censys, BGP (RIPEstat), PeeringDB, Wappalyzer, BuiltWith, HTTP Archive. |
| 14 | **D5** Climate / Environment Sources | FEMA, NOAA CDO, USFS fire, USGS seismic, Copernicus, ERA5, CDP, ENERGY STAR, TRI, Superfund, NRC. |
| 15 | **A4** D&O Maturation | Stanford SCAC, Dodd-Frank WB, ISS, proxy recs, board refreshment, CEO tenure, restatements; 28+ signals; 80+ inf fns. |
| 16 | **A5** FI Maturation | FFIEC Call Reports, UBPR, BSA/AML, CRA, NAIC RBC, Chainalysis-proxy, Travel Rule; 30+ signals; 85+ inf fns. |
| 17 | **A6** Aerospace Maturation | OpenSky, ICAO, ASIAS, FSIMS depth, Part 145 band; 30+ signals; 80+ inf fns. |
| 18 | **A7** Marine Maturation | AIS dark-activity, spoofing, Paris/Tokyo MoU, class transfer, CIC, FoC, STS; 30+ signals; 80+ inf fns. |
| 19 | **A8** Cyber/PI/Energy Finishing | Add saas_platform, aiml_vendor, clinical_research, media_tech, hydrogen, nuclear sub-configs; retrofit expectation_level + routing_constraints across all three. |
| 20 | **B1** Medical Professional Liability | `coverages/medprof/` with 5 sub-configs. |
| 21 | **B2** Workers' Compensation (standalone) | `coverages/wc/` with 6 sub-configs; casualty_wc deprecated. |
| 22 | **B3** Product Liability / Recall | `coverages/prodlib/` with 5 sub-configs. |
| 23 | **B4** Environmental Impairment | `coverages/env_liab/` with 5 sub-configs; casualty_environmental becomes cross-walk alias. |
| 24 | **E3** Confidence Calibration Harness | Reliability curves; confidence-scaling flagging. |

### Q3 — Wave 2 Coverages & Evidence Infrastructure

| Order | Phase | Deliverable |
|-------|-------|-------------|
| 25 | **D4** IP / Innovation Sources | USPTO, EPO Ops, OpenAlex, CrossRef, Semantic Scholar. |
| 26 | **D6** Sector Telemetry Sources | OpenSky, ICAO registry, ASIAS, AIS Hub, Marine Cadastre, EMSA, Paris/Tokyo MoU, PHMSA, BSEE detail, NERC. |
| 27 | **B5** Construction / CAR / OCIP | `coverages/construction/` with 5 sub-configs. |
| 28 | **B6** Event Cancellation / Contingency | `coverages/event/` with 5 sub-configs. |
| 29 | **B7** Political Violence & Terrorism | `coverages/pvt/` with 4 sub-configs. |
| 30 | **B8** Tech E&O (standalone) | `coverages/teo/` with 5 sub-configs. |
| 31 | **E1** Rust dsi-core Role Decision | Either adopt (scoring hot path via PyO3, measure p99) or retire from CI. |
| 32 | **E4** Per-Tenant Config Overlays | `coverages/{name}/overlays/{tenant_id}.yaml`. |
| 33 | **E9** Taxonomy Unification | One canonical 7-category list enforced in schema validator. |

### Q4 — Wave 3 Coverages, Behavioural Derivatives, Commercial Readiness

| Order | Phase | Deliverable |
|-------|-------|-------------|
| 34 | **D7** Hiring / Behavioural Derivatives | Greenhouse/Lever/Ashby scrapers, Google Jobs; velocity rolling-delta wired into `world_engine/drift/detector.py`. |
| 35 | **D8** Cost-Aware Signal Broker | Source router choosing cheapest satisfactory source; kill-switch env vars. |
| 36 | **B9** Reinsurance — Treaty & Fac | `coverages/reinsurance/` with 5 sub-configs; cedent cross-walk. |
| 37 | **B10** Crop / Parametric Weather | `coverages/crop/` with 5 sub-configs. |
| 38 | **B11** Specie / Fine Art | `coverages/specie/` with 4 sub-configs. |
| 39 | **B12** Captive / ART | `coverages/captive/` with 4 sub-configs. |
| 40 | **E2** Signal-Lineage Chain-of-Custody | `ExtractorResult.provenance` hash + audit-table link. |
| 41 | **E6** Drift-Alert → Referral Queue | Route drift alerts into `referrals.py`. |
| 42 | **E7** Rate-Filing Kit | `infrastructure/admin/rate_filing.py` produces SERFF-ready draft. |
| 43 | **E8** Evidence Dashboard | Admin endpoint exposing per-config real-signal-%, last-calibration, last-drift, last-golden. |
| 44 | **C5** Load + Chaos Testing | k6 scenarios; chaos-mesh manifests; nightly perf-report. |
| 45 | **C6** Regulatory Artefact Kit | Lloyd's MU&G, NAIC MRM, FCA FG21/3, GDPR DPIA, EU AI Act, SERFF templates under `docs/regulatory/`. |
| 46 | **E10** Stub Retirement | Move `signal_architecture/signals/extractors/stubs/` → `tests/fixtures/stub_extractors/`; block production imports. |
| 47 | **C4** Seed Consolidation (final) | Delete `seed_dsi_bench.py`, `seed_v5.py`, `synthetic_generator.py` from repo root; `python -m seed init` is the only path. |

---

## Cross-Workstream File Ownership

| File / Path | First Touched | Final Touched |
|-------------|---------------|---------------|
| `alembic/versions/` | C1 | E7 (rate-filing audit tables) |
| `signal_architecture/signals/extractors/production/` | D1 | D8 |
| `signal_architecture/signals/extractors/stubs/` | — | E10 (moves to tests) |
| `coverages/<existing>/config.yaml` | A1 | A8 |
| `coverages/<new>/config.yaml` | B1 | B12 |
| `infrastructure/builder/signal_library.py` | A1 | D8 |
| `infrastructure/builder/cli.py` | E2 | E8 |
| `infrastructure/api/routes/` | E6 | E8 |
| `world_engine/drift/detector.py` | D7 | E6 |
| `.github/workflows/ci.yml` | C1 | E5 |
| `deploy/kubernetes/` | C1 | C2 |
| `seed/` (new package) | C4 (interim) | C4 (final) |
| `docs/regulatory/` | C6 | C6 |
| `tests/fixtures/golden_entities/` | E5 | B12 |

---

## Parallelism Opportunities

Phases that share no file ownership can run concurrently:

- **Q1**: E5 + D1 can run in parallel with A1–A3 once the config gate (E2) is in place.
- **Q2**: A4–A8 and B1–B4 share only `infrastructure/builder/signal_library.py` — schedule A4–A8 first weekly, B1–B4 second weekly.
- **Q3**: Every B-wave-2 phase is independent of every other; four engineers can work in parallel.
- **Q4**: D7, E2, E6 share `world_engine/` — serialise within that cluster; B9–B12 parallel.

---

## Gate Criteria Between Quarters

- **Exit Q1**: Config health gate enforcing in CI; golden-entity suite green for existing coverages; FPR + Property + Casualty at Mature; CI deploys a test image to a real staging cluster.
- **Exit Q2**: Every existing coverage at Mature; first four new coverages shipped and green in regression; confidence-calibration harness producing reliability curves.
- **Exit Q3**: Second wave of new coverages shipped; IP + sector telemetry extractors live; rust/core decision made and implemented.
- **Exit Q4**: All 22 coverages at Mature; seed consolidated to single CLI; stubs relocated; evidence dashboard live; regulatory artefact kit drafted; perf + chaos green.
