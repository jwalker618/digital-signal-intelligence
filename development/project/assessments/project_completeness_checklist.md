# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Project Completeness Checklist

| Item | Value |
|-|-|
|Version|1.0.0|
|Date|February 2026|
|Classification|Project Assessment|

---

## Purpose

A repeatable, comprehensive checklist for assessing the completeness of the DSI framework against its defining specifications: the Whitepaper, Vision Paper, Foundational Principles, Configuration Schema (v2.3.0), and implementation architecture. Run this periodically to identify gaps, track progress, and ensure nothing is missed.

## Automated Assessment Tools

The following automated tools should be used to verify checklist items marked **(Test)**:

| Tool | Purpose | Command |
|-|-|-|
| **Project Assessor** | Full project assessment | `python development/project/assessments/scripts/dsi_assessor.py` |


**Recommended Assessment Workflow:**

1. Run `python development/project/assessments/scripts/dsi_assessor.py` for full project status
2. Review failures and warnings
3. Fix critical failures before proceeding
4. Document any accepted warnings with rationale

See `README.md` in this directory for detailed assessment methodology.

## How to Use

Each item is a concrete, verifiable assertion. When running an assessment:

| Status | Meaning |
|-|-|
| **PASS** | Fully implemented and demonstrable |
| **PARTIAL** | Exists but incomplete, uses stubs, or lacks coverage |
| **FAIL** | Missing, broken, or not started |
| **N/A** | Not applicable to current scope |

Items annotated with **(Test)** can and should be verified programmatically. Items annotated with **(Manual)** require human judgment.

---

# coverages (`coverages/`)

## Configuration Documentation

- Is there a `logic.md` file for every `config.yaml` file which explains the logic / decision making used? **(Test)**
  - Does this include each configuration under the config (e.g., `cyber_general` and `cyber_sme` under `cyber`)? **(Test)**
  - Does this show risk, loss, and exposure weights that add to 1? **(Test)**
  - Does this explain the rationale for signal selection and weighting for this coverage?
  - Does this document which signal groups are most important for this coverage and why? **(Test)**

## Premium Methodology

- Is the premium methodology contextually valid against routing constraints? **(Test)**
  - **Scalability Trap Check:** If `PREMIUM_BASE` is used, the validator MUST confirm a `routing_constraint` exists that caps the maximum size of the entity (e.g., `revenue <= 50M` or `hull_value <= 50M`).
  - **Enterprise Enforcement:** If the config lacks size constraints or explicitly targets large limits/revenues, the validator MUST enforce the use of `MULTIPLIER` (Rate × Basis).
- When MULTIPLIER is used, is the `basis` field listed in `minimum_viable_input`? **(Test)**
- Are the tier rate progressions actuarially monotonic? **(Test)**
  - Validator must assert that Tier 1 < Tier 2 < Tier 3 < Tier 4 < Tier 5 (prices strictly increase as risk score drops).
  - Validator must assert the penalty ratio (Tier 5 price / Tier 1 price) is >= 2.0.
- Does the Pricing block contain valid Anchors (`base_limit_reference` and `base_deductible_reference`)? **(Test)**
- Does the ILF Curve explicitly contain the `base_limit_reference` with a factor of exactly 1.00? **(Test)**
- Do the Deductible Factors explicitly contain the `base_deductible_reference` with a factor of exactly 1.00? **(Test)**

## Schema Compliance

- Is the `config.yaml` and all underlying configurations compliant with the `master_config_layout.yaml`? **(Test)**
  - Are all required components included? This should include: `direct_queries`, `signal_registry`, `groups`, `risk_tier_bands`, `loss_tier_bands`, `exposure`, `limit_configuration`, `pricing` (including correct anchors: `base_limit_reference` and `base_deductible_reference`)
- Does the config pass `infrastructure/validation/config_validator.py` with 0 errors, 0 warnings? **(Test)**
- Is the schema version declared in metadata v2.2.0 or later? **(Test)**

## Per-Coverage Verification

Repeat for each coverage within coverages/

| Check | Testable | Description |
|-|-|-|
| Config parses | Test | YAML parses without syntax errors |
| Validator passes | Test | 0 errors, 0 warnings from config_validator |
| Metadata complete | Test | name, version, product_types, applicable_markets, minimum_viable_input, min_premium, default_currency |
| model_specificity set | Test | Integer 1-5 present in metadata |
| routing_constraints defined | Test | Array present in metadata (may be empty) |
| Signal count adequate | Test | signal_registry contains >= 15 signals |
| Signal IDs unique | Test | No duplicate IDs within signal_registry |
| Inference functions exist | Test | Every `inference_utility_function` is registered in the inference registry |
| Proxy tiers assigned | Test | Every signal has DIRECT_OBSERVABLE, INFERRED_PROXY, or COHORT_INFERENCE |
| Three-layer dimensions | Test | Every scored signal has risk, loss (frequency+severity), and exposure (size+complexity) |
| Group IDs match | Test | Every group_id in signals matches a group in the groups section |
| Risk weights sum to 1.0 | Test | Per group and across groups |
| Loss weights sum to 1.0 | Test | Per group and across groups |
| Exposure weights sum to 1.0 | Test | Per group and across groups |
| Risk tier bands correct | Test | 5 bands, non-overlapping, contiguous, covering 0-1000 |
| Loss tier bands correct | Test | Non-overlapping, contiguous, floor/cap constraints defined |
| Exposure bands correct | Test | Size and complexity bands defined with methods and modifiers |
| Direct queries <= 10 | Test | Maximum 10 direct queries per configuration |
| Query actions valid | Test | Only FLAG, MODIFIER, REFER used in query_condition |
| ILF curve defined | Test | Per product_type, with base_limit matching base_limit_reference |
| Deductible factors defined | Test | Per product_type |
| Taxes/fees rate defined | Test | taxes_fees_rate present |
| Coverage docs exist | Test | `coverage/{coverage}/logic.md` exists and is current |
| Legacy fields removed | Test | Ensure deductible_credits and deductible_buy_down_rates are not present in any config (Phase 5 deprecation). |
| Routing exclusivity | Test | Ensure SME and Corporate configs within the same coverage have mutually exclusive routing_constraints (e.g., revenue <= 50M vs revenue > 50M) to prevent Arbiter collisions. |
| Dynamic input validation | Test | Does the API schema require fields used in routing_constraints (like revenue, hull_value) to be present in the submission payload before initiating the Multiplexer? |


## Cross-Coverage Consistency

- Do all coverages follow identical structural pattern? **(Test)**
- Is the coverage crosswalk documented (`signal_architecture/signals/cross_walk/`)? **(Manual)**
- Are common concepts (credit rating, certification, leadership stability, regulatory actions, breach history, litigation history, industry engagement) mapped across coverages? **(Manual)**
- Do all configs pass the same validator with 0 errors? **(Test)**

---

# demo (`demo/`)

## Demo Server

- Does the demo server start without errors? (`demo/server.py`) **(Test)**
- Does `demo/index.html` serve correctly through the demo server? **(Test)**

## Coverage Examples

- Does `demo/examples/run_{coverage}.py` run without error? **(Test)**
- Are all `sys.path.insert` paths correct (3 levels up to repo root)? **(Test)**
- Do the examples produce valid WorkflowResult output with all required fields? **(Test)**
- Do the examples demonstrate all three pricing decisions (APPROVE, REFER, DECLINE)? **(Manual)**

---

# deploy (`deploy/`)

## Deployment Documentation

- Is the `deployment_guide.md` comprehensive and include all necessary steps to deploy DSI? **(Manual)**
  - Does it cover prerequisites (Python, PostgreSQL, Redis, Rust toolchain)?
  - Does it cover environment variable configuration?
  - Does it cover database migration (Alembic)?
  - Does it cover Docker build and run?
  - Does it cover Kubernetes deployment?
  - Does it cover monitoring setup (Prometheus)?
  - Does it cover health check verification?
  - Does it cover rollback procedures?

## Docker

- Does `Dockerfile` exist at project root? **(Test)**
- Does `docker-compose.yml` exist at project root? **(Test)**
- Does `deploy/docker/docker-compose.prod.yml` exist? **(Test)**
- Does the Docker container build successfully? **(Test)**
- Does the container start and serve the API on the expected port? **(Test)**
- Are secrets passed via environment variables (not baked into image)? **(Manual)**

## Kubernetes

- Does `deploy/kubernetes/deployment.yaml` exist with correct image reference? **(Test)**
- Does `deploy/kubernetes/service.yaml` exist with correct port mapping? **(Test)**
- Does `deploy/kubernetes/hpa.yaml` exist with reasonable scaling thresholds? **(Manual)**
- Does `deploy/kubernetes/ingress.yaml` exist? **(Test)**
- Does `deploy/kubernetes/configmap.yaml` exist with non-secret configuration? **(Test)**
- Does `deploy/kubernetes/secrets-template.yaml` exist and use environment variable references (no hardcoded secrets)? **(Test)**
- Does `deploy/kubernetes/namespace.yaml` exist? **(Test)**
- Does `deploy/kubernetes/kustomization.yaml` exist and reference all manifests? **(Test)**

## Monitoring

- Does `deploy/monitoring/prometheus-config.yaml` exist? **(Test)**
- Are alert rules defined for key metrics (latency, error rate, throughput)? **(Manual)**
- Is the application's metrics endpoint (`/metrics`) configured for Prometheus scraping? **(Test)**

## CI/CD Pipeline

- Is there a CI/CD configuration (GitHub Actions, GitLab CI, etc.)? **(Test)**
- Does it include: Rust build stage? **(Test)**
- Does it include: Python test stage? **(Test)**
- Does it include: Integration test stage? **(Test)**
- Does it include: Docker build + push stage? **(Test)**
- Does it include: Staging deploy stage? **(Test)**
- Does it include: Production deploy stage? **(Test)**

---

# docs (`docs/`)

## Whitepaper Compliance

Reference: `docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf`

- Is the project correctly reflective of the whitepaper? **(Manual)**

### 10 Foundational Principles

| # | Principle | Check |
|-|-|-|
| 1 | External Observability | Is signal architecture designed for external-only data collection? |
| 2 | Machine Readability | Are all signals machine-extractable and algorithmically scored? |
| 3 | Network Authority | Is the organisational graph with PageRank implemented? |
| 4 | Behavioural Inference | Does proxy tier weighting prefer observable over self-reported? |
| 5 | Absence as Signal | Do inference functions measure absence of expected signals? |
| 6 | Structured Data Utilisation | Are authoritative third-party data feeds integrated? |
| 7 | Minimal Direct Inquiry | Are direct queries constrained to max 10 binary questions? |
| 8 | Organisational Assessment | Is entity-level (not asset-level) scoring the primary unit? |
| 9 | Simplicity in Scoring | Is the flow Signal->Score->Tier->Price clear and auditable? |
| 10 | Agentic Readiness | Can every component execute without human interpretation? |

### Signal Architecture Promises

- Are 7 signal categories implemented? **(Test)**
- Is signal normalisation (0-100) implemented for all types? **(Test)**
- Is confidence scoring (0-1) tracked throughout the pipeline? **(Test)**
- Is proxy tier classification (DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE) implemented? **(Test)**
- Is temporal decay (TTL per signal) implemented? **(Test)**
- Is the target of 200-400 signals per submission achievable (registry + library)? **(Manual)**
- Is absence-as-signal measurement implemented in at least one inference function? **(Manual)**

### Processing Workflow Promises

- Is the 6-phase, 14-step workflow complete? **(Test)**
- Does discovery resolve entity from minimal input (name + optional domain)? **(Test)**
- Do three assessment layers run in parallel? **(Test)**
- Is < 60 second time to quote achievable? **(Test)** — benchmark target ~80ms
- Is < $10 cost per submission architecturally supported? **(Manual)**
- Is there a complete audit trail for every decision? **(Test)**
- Is model versioning (content-addressable config hashing) working? **(Test)**

### Operational Targets

- Can 60-80% straight-through processing be achieved (with real extractors)? **(Manual)** — requires production data
- Is every pricing output traceable: signal -> score -> tier -> premium? **(Test)**

## Vision Paper Compliance

Reference: `docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf`

- Is the project correctly reflective of the vision paper? **(Manual)**

### Organisational Graph (World Model)

- Does the graph have 6 node types and 6 edge types? **(Test)**
- Does PageRank authority propagation work? **(Test)**
- Does risk propagation across graph edges work? **(Test)**
- Is graph construction from live signal data implemented? **(Test)**
- Are Rust accelerators for graph algorithms working? **(Test)**

### Behavioural Derivatives

- Is Entropy (control decay) calculated? **(Test)**
- Is Velocity (operational overload) calculated? **(Test)**
- Is Drift (emerging fragility) calculated? **(Test)**
- Is Fragility calculated? **(Test)**
- Is Concentration calculated? **(Test)**
- Are derivatives tracked as time-series (not just point-in-time)? **(Test)** — Vision paper requirement
- Is leading indicator detection (6-12 month advance warning) implemented? **(Manual)**

### Continuous Monitoring

- Is continuous observation implemented (not just point-in-time)? **(Test)**
- Is signal refresh scheduling (TTL-based) implemented? **(Test)**
- Is delta detection (score changes between assessments) implemented? **(Test)**
- Is derivative time-series tracking implemented? **(Test)**
- Is an alert pipeline (threshold triggers) implemented? **(Test)**
- Is Nyquist-Shannon compliance addressed (adequate sampling frequency)? **(Manual)**
- Is cohort migration tracking (peer group movement over time) implemented? **(Test)**
- Are API endpoints for monitoring status/alerts exposed? **(Test)**

### Simulation Engine

- Are graph state snapshots (save/restore) implemented? **(Test)**
- Is counterfactual analysis ("what if" scenarios) implemented? **(Test)**
- Is shock propagation (cascade effects through graph) implemented? **(Test)**
- Is a portfolio impact calculator implemented? **(Test)**
- Are API endpoints for simulation exposed? **(Test)**

### Portfolio Optimisation

- Is marginal submission impact on portfolio volatility calculated? **(Test)**
- Is correlation-aware pricing implemented? **(Test)**
- Is dynamic capital allocation implemented? **(Test)**

### Homeostasis (Closed-Loop Carrier)

- Does drift detection trigger automatic intervention? **(Test)**
- Are intervention actions defined (notification, repricing, non-renewal)? **(Test)**
- Is there a continuous feedback loop between monitoring and pricing? **(Test)**

### Paradigm Shift Metrics

| Dimension | Target State | Assessment |
|-|-|-|
| Data source | Direct observation (not self-report) | Is data from external APIs, not insured submissions? |
| Analysis type | Simulation (not static assessment) | Can the system simulate scenarios, not just assess? |
| Response type | Prevention / homeostasis (not reactive) | Does the system proactively intervene on drift? |
| Observation frequency | Continuous (not one-shot) | Is monitoring continuous, not just at submission time? |
| Feature basis | Behavioural derivative time-series | Are derivatives tracked over time, not just point-in-time? |
| Decision type | Real-time automated | Are decisions real-time and fully automated for Tier 1-3? |

## Core Documentation Inventory

| Document | Path | Exists | Current |
|-|-|-|-|
| Foundational Principles | `docs/overview/Foundational Principles.md` | | |
| Configuration Architecture | `docs/overview/Configuration_Architecture.md` | | |
| Premium Calculation Methodology | `docs/overview/Premium_Calculation_Methodology.md` | | |
| Agent Interaction Spec | `docs/agent_interaction/dsi_specification.md` | | |
| Whitepaper (PDF) | `docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf` | | |
| Vision Paper (PDF) | `docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf` | | |
| Pitch Deck (PDF) | `docs/overview/Pitch_deck.pdf` | | |
| PageRank Precedent (PDF) | `docs/overview/The_PageRank_Precedent.pdf` | | |
| Retrospective Case Studies (PDF) | `docs/case_studies/Retrospective_loss_case_studies.pdf` | | |
| SKILL.md (Development Guide) | `SKILL.md` | | |
| README.md (Project Overview) | `README.md` | | |
| CHANGELOG.md | `CHANGELOG.md` | | |
| CONTRIBUTING.md | `CONTRIBUTING.md` | | |

---

# infrastructure (`infrastructure/`)

## API (`infrastructure/api/`)

- Does the FastAPI application start without errors? **(Test)**
- Is structured JSON logging with correlation IDs implemented? **(Test)**
- Is Prometheus metrics instrumentation implemented? **(Test)**
- Is rate limiting middleware implemented (in-memory + Redis backends, per-API-key tiers)? **(Test)**
- Is JWT and API key authentication implemented (`infrastructure/api/auth/`)? **(Test)**

### API Routes

| Route File | Path | Functional |
|-|-|-|
| Submissions | `infrastructure/api/routes/submissions.py` | |
| Quotes | `infrastructure/api/routes/quotes.py` | |
| Referrals | `infrastructure/api/routes/referrals.py` | |
| Analytics | `infrastructure/api/routes/analytics.py` | |

- Is there a health check endpoint? **(Test)**
- Are all 32 documented endpoints functional? **(Test)**
- Is the API schema (request/response models) complete with `country_hint` field? **(Test)**
- Are API error responses structured and informative? **(Manual)**

## Database (`infrastructure/db/`)

- Do SQLAlchemy ORM models exist (`infrastructure/db/models.py`)? **(Test)**
- Is the 8-table initial schema defined? **(Test)**
- Does the Alembic migration exist (`alembic/versions/001_initial_schema.py`)? **(Test)**
- Does the migration run successfully against a fresh database? **(Test)**
- Does the repository pattern for data access work (`infrastructure/db/repositories.py`)? **(Test)**
- Is database configuration externalised (`infrastructure/db/config.py`)? **(Test)**
- Are lazy DB engine singletons used (no hard FastAPI dependency)? **(Test)**
- Does dual storage work: PostgreSQL persistence + in-memory fallback? **(Test)**
- Are lazy imports in `infrastructure/__init__.py` preventing import failures? **(Test)**

## Analytics (`infrastructure/analytics/`)

- Does the performance metrics module exist and work? **(Test)**
- Does the portfolio analytics module exist and work? **(Test)**
- Does the signal analytics module exist and work? **(Test)**
- Does cohort analysis work? **(Test)**
- Are analytics types defined? **(Test)**
- Is import order correct (no circular dependencies)? **(Test)**

## Coverage Builder (`infrastructure/builder/`)

- Does the builder generate v2.0+ compliant configs? **(Test)**
- Does the validator enforce v2.0+ schema rules? **(Test)**
- Is the signal library integrated with the metadata registry? **(Test)**
- Does `python -m infrastructure.builder.cli build` produce a valid config? **(Test)**
- Does `python -m infrastructure.builder.cli validate` correctly identify errors? **(Test)**
- Does `python -m infrastructure.builder.cli list-signals` list all registered signals? **(Test)**
- Does `python -m infrastructure.builder.cli list-industries` list available industries? **(Test)**
- Does builder output pass its own validator? **(Test)**
- Does the builder generate all required sections: signal_registry, groups, risk_tier_bands, loss_tier_bands, exposure, pricing? **(Test)**
- Does the builder enforce score_condition rules (FLAG|MODIFIER|REFER only, no DECLINE at signal level)? **(Test)**
- Does the builder output match canonical structure: `coverage_id -> config_name -> {metadata, signal_registry, ...}`? **(Test)**

## Configuration Validator (`infrastructure/validation/`)

- Does `config_validator.py` exist? **(Test)**
- Does it validate all schema structure requirements? **(Test)**
- Does it validate weight sums (1.0 per group per layer)? **(Test)**
- Does it validate score_condition action rules? **(Test)**
- Does it validate tier band non-overlap and contiguity? **(Test)**
- Does it validate MULTIPLIER basis is in minimum_viable_input? **(Test)**
- Does it validate that all referenced inference functions exist? **(Test)**
- Does it validate signal/group ID uniqueness? **(Test)**
- Do all 7 coverage configs pass validation with 0 errors? **(Test)**

## Integrations (`infrastructure/integrations/`)

- Does the email notification module exist? **(Test)**
- Does the document generation module exist? **(Test)**
- Does the webhook handler exist? **(Test)**
- Are integrations functional or stub-only? **(Manual)**

---

# layers (`layers/`)

## Risk Layer (`layers/risk/`)

### 14-Step Workflow Completeness

| Step | Name | Component | Functional |
|-|-|-|-|
| 0 | Website discovery | `workflow.py` calls discovery engine | |
| 1 | Model configuration instantiation | `config_manager.py` — content-addressable storage | |
| 2 | Model data file creation | `model_data.py` — signal capture + versioning | |
| 3 | Minimum viable input verification | `workflow.py` — required field check | |
| 4 | Signal extraction | `scorer.py` — execute all signal pipelines | |
| 5a | Risk composite score | `scorer.py` — weighted 0-1000 | |
| 5b | Exposure magnitude score | Parallel — exposure layer | |
| 5c | Loss propensity score | Parallel — loss layer | |
| 6 | Signal conditions evaluation | `scorer.py` — FLAG, MODIFIER, REFER | |
| 7 | Direct query evaluation | `query_evaluator.py` — response processing | |
| 8 | Maximum tier override | `scorer.py` — worst-case from Steps 6 & 7 | |
| 9a | Final risk tier capture | Model data — tier used for pricing | |
| 9b | Final exposure band capture | Model data — exposure band + complexity | |
| 9c | Final loss propensity capture | Model data — loss band + cohort + trend | |
| 10 | Base premium generation | `pricer.py` — tier x exposure x loss | |
| 10.5 | Traditional modifiers (optional) | `modifiers/` — loss history, exposure, rating | |
| 11 | Modifier application | `pricer.py` — multiplicative with floor/cap | |
| 12 | Limit band scaling | `pricer.py` — ILF curve + deductible factors | |
| 13 | Decision output | `workflow.py` — APPROVE, REFER, DECLINE | |

### Core Component Files

| File | Purpose | Exists | Functional |
|-|-|-|-|
| `layers/risk/workflow.py` | Full 14-step orchestration | | |
| `layers/risk/config_manager.py` | YAML parsing, SHA-256 hashing, content-addressable storage | | |
| `layers/risk/scorer.py` | Signal extraction (Step 4), scoring (Step 5), conditions (Step 6) | | |
| `layers/risk/query_evaluator.py` | Direct query evaluation (Step 7) | | |
| `layers/risk/pricer.py` | Premium calculation (Steps 10-12) | | |
| `layers/risk/model_data.py` | Model data file management (Step 2) | | |
| `layers/risk/types.py` | WorkflowResult, ModelVersion, DecisionType, AppliedModifier | | |
| `layers/risk/modifiers/` | Traditional modifier implementations | | |

### WorkflowResult Output Completeness

- Does `WorkflowResult` include `entity_id`, `coverage`, `entity_name`? **(Test)**
- Does it include `discovered_domain` and `discovery_confidence`? **(Test)**
- Does it include `signal_scores` (dict of all individual signal scores)? **(Test)**
- Does it include `composite_score` (0-1000)? **(Test)**
- Does it include `risk_tier` (pre-override) and `tier` (post-override)? **(Test)**
- Does it include `loss_tier` and `exposure_tier`? **(Test)**
- Does it include `tier_label` and `decision` (APPROVE|REFER|DECLINE)? **(Test)**
- Does it include `recommended_premium` and `premium_options`? **(Test)**
- Does it include `applied_modifiers` list? **(Test)**
- Does it include `model_version` (config hash, signal coverage %)? **(Test)**
- Does it include `processing_time_ms`? **(Test)**

### Pricing Methods

- Does PREMIUM_BASE method work (fixed base premium per tier)? **(Test)**
- Does MULTIPLIER method work (rate x basis value)? **(Test)**
- Does ILF (Increased Limit Factor) scaling work? **(Test)**
- Are deductible factors applied correctly? **(Test)**
- Is taxes/fees rate applied? **(Test)**
- Do traditional modifiers (LossHistoryModifier, ExposureModifier, ExternalRatingModifier) work? **(Test)**

## Loss Correlation Layer (`layers/loss/`)

- Does the loss scorer exist and work (`layers/loss/scorer.py`)? **(Test)**
- Does the loss correlation matrix exist (`layers/loss/matrix.py`)? **(Test)**
- Does the config adapter convert risk tiers to loss tiers (`layers/loss/config_adapter.py`)? **(Test)**
- Does loss frequency scoring work? **(Test)**
- Does loss severity scoring work? **(Test)**
- Is the combined modifier = frequency_modifier x severity_modifier? **(Test)**
- Are floor/cap constraints applied correctly? **(Test)**
- Does cohort assignment work (signal-derived, not industry-code-based)? **(Test)**
- Is correlation direction handled correctly (negative correlations inverted)? **(Test)**
- Does confidence gate pricing (low confidence prevents auto-adjustments)? **(Test)**
- Is there graceful fallback when loss data is unavailable? **(Test)**

## Exposure Shadow Layer (`layers/exposure/`)

- Does the exposure scorer exist and work (`layers/exposure/scorer.py`)? **(Test)**
- Does size dimension scoring work? **(Test)**
- Does complexity dimension scoring work? **(Test)**
- Does proxy tier determine confidence (DIRECT_OBSERVABLE > INFERRED_PROXY > COHORT_INFERENCE)? **(Test)**
- Does output use ranges (not point estimates)? **(Test)**
- Does high exposure + low confidence trigger referral? **(Test)**
- Does complexity multiply exposure for pricing adjustment? **(Test)**

## Three-Layer Integration

- Do all three layers run in parallel (Steps 5a/5b/5c)? **(Test)**
- Do the same signal outputs feed all three layers (different weights)? **(Test)**
- Do all layers complete before pricing (Steps 9a/9b/9c before Step 10)? **(Test)**
- Does pricing use all three outputs: Risk Tier x Exposure Band x Loss Modifier? **(Test)**
- Can referral triggers come from all three layers? **(Test)**

---

# rust (`rust/`)

## Rust Accelerators (`rust/dsi-core/`)

- Does `Cargo.toml` exist with PyO3, serde, rayon dependencies? **(Test)**
- Does `src/lib.rs` (module entry point) exist? **(Test)**
- Does `src/graph.rs` (PageRank, risk propagation, exposure aggregation) exist? **(Test)**
- Does `src/derivatives.rs` (entropy, velocity, drift, concentration, fragility) exist? **(Test)**
- Does `src/validation.rs` (YAML config validation) exist? **(Test)**
- Do PyO3 bindings expose Rust functions to Python? **(Test)**
- Do Criterion benchmarks exist (`rust/dsi-core/benches/`)? **(Test)**
- Is release build with LTO configured? **(Test)**
- Does `maturin develop` produce an installable wheel? **(Test)**
- Do Rust PageRank results match Python PageRank results? **(Test)**
- Do Rust derivative results match Python derivative results? **(Test)**

---

# schemas (`schemas/`)

- Does `schemas/organisational_graph.yaml` exist? **(Test)**
- Does it define the 6 node types (COMPANY, SUBSIDIARY, DOMAIN, PERSON, VENDOR, ASSET)? **(Test)**
- Does it define the 6 edge types (OWNS, OPERATES, EMPLOYS, PARTNERS_WITH, DEPENDS_ON, CERTIFIES)? **(Test)**
- Is the schema consistent with the graph implementation in `signal_architecture/graph/types.py`? **(Test)**
- Does `coverages/master_config_layout.yaml` exist and define the v2.2.0 schema? **(Test)**

---

# signal_architecture (`signal_architecture/`)

## Signal Pipeline (4-Step Process)

- Does the extractor base class exist (`signal_architecture/signals/extractors/base.py`)? **(Test)**
- Do aggregator implementations exist (`signal_architecture/signals/aggregators/`)? **(Test)**
- Do categoriser implementations exist (`signal_architecture/signals/categorisers/`)? **(Test)**
- Does the inference function registry exist (`signal_architecture/signals/inference/registry.py`)? **(Test)**
- Does the pipeline flow Extractor -> Aggregator -> Categoriser -> Inference work end-to-end? **(Test)**

## Core Types

- Does `SignalType` enum define all 7 signal types? **(Test)**
- Does `ExtractorResult` dataclass have all fields: success, data, source, extracted_at, ttl_seconds, error, metadata, from_cache? **(Test)**
- Is TTL-based caching supported (ttl_seconds, expires_at)? **(Test)**
- Is signal normalisation to 0-100 scale enforced? **(Test)**
- Is confidence scoring (0-1) tracked throughout? **(Test)**

## Extractors

### Stub Extractors

- Does StubExtractor base exist? **(Test)**
- Do coverage-specific stubs exist for all 7 coverages? **(Test)**
- Do stubs return structurally realistic data? **(Manual)**
- Does `FEATURE_USE_STUBS` environment flag control stub/production mode? **(Test)**

### Production Extractors

**Corporate Registry:**
| Extractor | Source | Exists | Functional |
|-|-|-|-|
| LEI | GLEIF | | |
| ABN | Australia Business Register | | |
| Companies House | UK Companies House | | |
| India MCA | Ministry of Corporate Affairs | | |

**DNS / Security:**
| Extractor | Source | Exists | Functional |
|-|-|-|-|
| TLS grade | SSL Labs methodology | | |
| DNSSEC status | DNS queries | | |
| SPF record | DNS queries | | |
| DKIM record | DNS queries | | |
| DMARC record | DNS queries | | |
| DNS complexity | DNS analysis | | |
| Security headers | HTTP header inspection | | |

**Network:**
| Extractor | Source | Exists | Functional |
|-|-|-|-|
| Network exposure | Port scanning | | |
| IP footprint | IP analysis | | |
| Subdomain enumeration | DNS + crawl | | |
| Certificate analysis | Certificate transparency | | |

**Security:**
| Extractor | Source | Exists | Functional |
|-|-|-|-|
| Breach history | HaveIBeenPwned | | |
| Security rating | (paid - stub available) | | |
| Dark web monitoring | (paid - stub available) | | |

**Market / Structural:**
| Extractor | Source | Exists | Functional |
|-|-|-|-|
| Job postings | Career page / job board APIs | | |
| Company funding | Funding data sources | | |
| Employee count | Public data sources | | |
| Industry classification | SIC/NAICS lookup | | |

**Paid (Stub Mode):**
| Extractor | Source | Exists | Stub Functional |
|-|-|-|-|
| Shodan | Shodan API | | |
| VirusTotal | VirusTotal API | | |
| Dun & Bradstreet | D&B API | | |

### Extractor Infrastructure

- Does the unified extractor resolver support stub/production/hybrid modes? **(Test)**
- Does jurisdiction-aware routing work (`signal_architecture/signals/routing/`)? **(Test)**
- Does the extractor factory create the correct extractor based on signal ID and mode? **(Test)**
- Do production extractors gracefully degrade when API is unavailable? **(Test)**

## Inference Functions

- Does `@register_inference_function()` decorator register functions in global registry? **(Test)**
- Does `get_inference_function(name)` retrieve functions by name? **(Test)**
- Does `list_inference_functions()` return all registered functions? **(Test)**

| Coverage | Source File | Functions Exist |
|-|-|-|
| Aerospace | `signal_architecture/signals/inference/functions/aerospace/signals.py` | |
| Cyber | `signal_architecture/signals/inference/functions/cyber/signals.py` | |
| D&O | `signal_architecture/signals/inference/functions/do/signals.py` | |
| Energy | `signal_architecture/signals/inference/functions/energy/signals.py` | |
| FI | `signal_architecture/signals/inference/functions/fi/signals.py` | |
| Marine | `signal_architecture/signals/inference/functions/marine/signals.py` | |
| PI | `signal_architecture/signals/inference/functions/pi/signals.py` | |
| Cross-coverage | `signal_architecture/signals/inference/functions/cross_coverage/signals.py` | |

- Does every `inference_utility_function` referenced in any coverage config resolve to a registered function? **(Test)**
- Does the metadata registry catalogue all signals with proxy tiers, TTLs, and extractor references? **(Test)**

## Discovery Engine

- Does `WebsiteDiscoveryEngine` exist (`signal_architecture/discovery/website_discovery.py`)? **(Test)**
- Does discovery resolve entity name + domain hint to primary website URL? **(Test)**
- Does discovery return confidence level (HIGH | MEDIUM | LOW | UNVERIFIED)? **(Test)**
- Does discovery handle missing domain hints gracefully? **(Test)**
- Does discovery feed Step 0 of the workflow? **(Test)**

## Orchestration

- Does `MultiCoverageOrchestrator` exist (`signal_architecture/orchestration/multi_coverage.py`)? **(Test)**
- Does locale detection work (`signal_architecture/orchestration/locale_detection.py`)? **(Test)**
- Can multiple coverages be assessed for the same entity in a single request? **(Test)**

## Multiplexer (Phase V4)

- Does `DSIMultiplexer` (signal broker) exist (`signal_architecture/multiplexer/broker.py`)? **(Test)**
- Does `ConfigArbiter` exist (`signal_architecture/multiplexer/arbiter.py`)? **(Test)**
- Does the arbiter rank by: validity -> confidence -> specificity -> margin? **(Test)**
- Does signal deduplication work (shared signals across configs)? **(Test)**
- Does `signal_completeness` metric prevent phantom approvals? **(Test)**
- Does integration with MultiCoverageOrchestrator work? **(Test)**
- Are routing constraints evaluated before signal execution? **(Test)**

## Organisational Graph

- Are graph types defined (`signal_architecture/graph/types.py`)? **(Test)**
- Does node factory create nodes from signals (`signal_architecture/graph/node_factory.py`)? **(Test)**
- Does edge inferencer create edges (`signal_architecture/graph/edge_inferencer.py`)? **(Test)**
- Does graph builder orchestrate full graph construction (`signal_architecture/graph/graph_builder.py`)? **(Test)**
- Does graph storage and serialisation work (`signal_architecture/graph/storage.py`)? **(Test)**

### Behavioural Derivatives

| Derivative | Calculator | Exists | Functional |
|-|-|-|-|
| Entropy (control decay) | `signal_architecture/graph/derivatives/calculator.py` | | |
| Velocity (operational overload) | Same | | |
| Drift (emerging fragility) | Same | | |
| Fragility (structural weakness) | Same | | |
| Concentration (dependency risk) | Same | | |

- Are derivatives currently point-in-time only (temporal tracking not yet implemented)? **(Test)**

### Propagation Algorithms

- Is PageRank implemented in Python (`signal_architecture/graph/propagation/algorithms.py`)? **(Test)**
- Is risk propagation across edges implemented? **(Test)**
- Is exposure aggregation across graph implemented? **(Test)**

---

# tests (`tests/`)

## Test Infrastructure

- Does `tests/conftest.py` exist with shared fixtures? **(Test)**
- Does `tests/README.md` exist with test execution instructions? **(Test)**
- Is pytest the configured test runner? **(Test)**
- Are tests organised by type: unit, integration, api, performance? **(Test)**

## Test File Status

### Unit Tests

| Test File | Import OK | Tests Pass | Module Tested |
|-|-|-|-|
| `tests/unit/test_analytics.py` | | | Analytics |
| `tests/unit/test_builder.py` | | | Coverage builder |
| `tests/unit/test_config_manager.py` | | | Config manager |
| `tests/unit/test_config_validator.py` | | | Config validator |
| `tests/unit/test_coverage_builder_v2.py` | | | Builder v2 |
| `tests/unit/test_graph.py` | | | Organisational graph |
| `tests/unit/test_loss_correlation.py` | | | Loss correlation |
| `tests/unit/test_model_data.py` | | | Model data files |
| `tests/unit/test_multi_coverage.py` | | | Multi-coverage |
| `tests/unit/test_multiplexer.py` | | | Multiplexer |
| `tests/unit/test_portfolio_analytics.py` | | | Portfolio analytics |
| `tests/unit/test_pricer.py` | | | Pricer |
| `tests/unit/test_query_evaluator.py` | | | Query evaluator |
| `tests/unit/test_routing.py` | | | Routing |
| `tests/unit/test_scorer.py` | | | Scorer |
| `tests/unit/test_traditional_modifiers.py` | | | Traditional modifiers |
| `tests/unit/test_workflow.py` | | | Workflow |

### Integration Tests

| Test File | Import OK | Tests Pass | Scope |
|-|-|-|-|
| `tests/integration/test_e2e_pipeline.py` | | | End-to-end workflow |
| `tests/integration/test_integrations.py` | | | External integrations |
| `tests/integration/test_loss_workflow.py` | | | Loss layer workflow |

### API Tests

| Test File | Import OK | Tests Pass | Scope |
|-|-|-|-|
| `tests/api/test_api.py` | | | REST endpoint tests |

### Performance Tests

| Test File | Import OK | Tests Pass | Scope |
|-|-|-|-|
| `tests/performance/test_benchmarks.py` | | | Latency benchmarks |

## Test Quality

- Do ALL test files import correctly (no ImportError on collection)? **(Test)**
- Is the happy path tested (Tier 1-2 auto-approval)? **(Test)**
- Is the referral flow tested (Tier 3-4 flag evaluation)? **(Test)**
- Is the decline path tested (Tier 5 auto-decline)? **(Test)**
- Are override scenarios tested (signal condition overrides tier)? **(Test)**
- Are edge cases tested (missing signals, low confidence, zero scores)? **(Test)**
- Is multi-coverage tested (same entity, multiple coverages)? **(Test)**
- Is config validation tested across all 7 coverages? **(Test)**
- Is the multiplexer tested (signal dedup, arbiter ranking, routing constraints)? **(Test)**

## Test Coverage Targets

| Component | Target | Met |
|-|-|-|
| Overall | 80% | |
| Signal Architecture (`signal_architecture/`) | 90% | |
| Risk Layer (`layers/risk/`) | 90% | |
| Loss Layer (`layers/loss/`) | 90% | |
| Exposure Layer (`layers/exposure/`) | 90% | |
| Infrastructure (`infrastructure/`) | 85% | |
| Graph (`signal_architecture/graph/`) | 85% | |

---

# Critical Rules Compliance

Reference: `SKILL.md` — Critical Rules section

## Core Framework Rules

- Is YAML the single source of truth (no hardcoded weights, thresholds, modifiers, tier definitions)? **(Test)**
- Are extractors stubs but structurally realistic with TTL caching? **(Test)**
- Are aggregators production-ready (handle real data when extractors upgraded)? **(Manual)**
- Do categorizers use the 12 parameterized types (reusable)? **(Test)**
- Is there one inference function per YAML `inference_utility_function`? **(Test)**
- Is the model layer coverage-agnostic (same code handles all 7 coverages)? **(Test)**
- Do all coverages follow identical file organization? **(Test)**
- Are individual signal scores 0-100? **(Test)**
- Is composite score 0-1000 (weighted sum x 10)? **(Test)**
- Is confidence tracked throughout the pipeline? **(Test)**
- Does TTL vary by source (appropriate per extractor)? **(Test)**
- Is there full auditability: signal -> score -> tier -> premium? **(Test)**

## Workflow Rules

- Do score_conditions support MODIFIER action (multiplicatively to premium)? **(Test)**
- Do direct queries support MODIFIER action (applied after base premium)? **(Test)**
- Do all matching MODIFIER conditions stack multiplicatively? **(Test)**
- Does the maximum tier override win (worst tier applied from multiple overrides)? **(Test)**
- Is every interaction versioned (model version tracking)? **(Test)**
- Does the MULTIPLIER method validate that basis field is in minimum_viable_input? **(Test)**

## Three-Layer Assessment Rules

- Are signals shared infrastructure (same outputs feed all three layers)? **(Test)**
- Do three layers run in parallel (not in sequence)? **(Test)**
- Are there different weights per layer for the same signals? **(Test)**
- Are all layers captured before pricing? **(Test)**
- Does pricing use all three outputs (Risk Tier x Exposure Band x Loss Modifier)? **(Test)**

## Loss Correlation Layer Rules

- Does loss propensity have caps/floors? **(Test)**
- Are cohorts signal-derived (not industry codes)? **(Test)**
- Is correlation direction handled correctly? **(Test)**
- Does confidence gate pricing? **(Test)**

## Exposure Shadow Layer Rules

- Does proxy tier determine confidence hierarchy? **(Test)**
- Is output in ranges (not point estimates)? **(Test)**
- Does high exposure + low confidence trigger referral? **(Test)**
- Does complexity multiply exposure? **(Test)**

---

# Performance Benchmarks

Reference: Phase P7

| Metric | Target | Measured | Met |
|-|-|-|-|
| End-to-end workflow | < 100ms | ~80ms | |
| Signal extraction | < 20ms avg | ~12ms | |
| Graph build | < 5ms | < 1ms | |
| Tier assignment | < 5ms | < 2ms | |
| Premium calculation | < 10ms | < 5ms | |
| API response time | < 200ms | | |

- Do performance benchmarks exist (`tests/performance/test_benchmarks.py`)? **(Test)**
- Do Rust benchmarks exist (`rust/dsi-core/benches/`)? **(Test)**
- Can the system handle batch processing of 1000+ assessments? **(Test)**

---

# Security & Governance

## Security

- Are there no hardcoded secrets in the codebase? **(Test)**
- Does the secrets template use environment variables? **(Test)**
- Is API authentication implemented (JWT + API key)? **(Test)**
- Is rate limiting preventing abuse? **(Test)**
- Is input validation present on API endpoints? **(Test)**
- Is there no SQL injection vulnerability (ORM-based queries)? **(Manual)**
- Is CORS configured appropriately? **(Manual)**

## Governance

- Do model changes produce a new SHA-256 hash (content-addressable storage)? **(Test)**
- Does the full audit trail capture every pricing decision? **(Test)**
- Does model version tracking link decisions to exact config? **(Test)**
- Is the Foundational Principles document versioned? **(Manual)**

---

# Assessment Summary Template

Use this template when recording assessment results:

```
Assessment Date: YYYY-MM-DD
Assessed By: [Name / System]
Codebase Stats: [X] Python files, [Y] lines, [Z] coverages

Section Scores:
  coverages:              ___ / ___ items
  demo:                   ___ / ___ items
  deploy:                 ___ / ___ items
  docs (whitepaper):      ___ / ___ items
  docs (vision paper):    ___ / ___ items
  infrastructure:         ___ / ___ items
  layers:                 ___ / ___ items
  rust:                   ___ / ___ items
  schemas:                ___ / ___ items
  signal_architecture:    ___ / ___ items
  tests:                  ___ / ___ items
  phase completion:       ___ / ___ phases
  critical rules:         ___ / ___ items
  performance:            ___ / ___ items
  security & governance:  ___ / ___ items

Overall: ___ / ___ items (___%)

Top Gaps:
1.
2.
3.

Recommended Next Steps:
1.
2.
3.
```
