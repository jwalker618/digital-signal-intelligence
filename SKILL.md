-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on any aspect of DSI project code.

# DSI Framework Development Guide

## Development Workflow

When starting any DSI work:

1. **Read this SKILL.md first**
1. **Review development/project/ for the relevant phase development plans**: Contains phase development plans
1. **Do not proceed with work without a phase development plan**: These are required
1. **Always seek clarification if a request is unclear**
1. **Reference YAML config** for the coverage you're working on
1. **Never hardcode** - if it's in YAML, read it from YAML
1. **Ensure the foundational principles are followed at all stages**: `docs/overview/Foundational Principles.md`
1. **Follow the standard patterns** - don't invent new structures
1. **Follow the 14-step workflow** - don't skip or reorder steps
1. **Check technical_pricing/cross_walk/by_coverage.json** for common concepts
1. **For coverage expansion phases**: Use the Coverage Expansion Pipeline -- author an expansion spec YAML, then run `python -m infrastructure.builder.cli expand --spec <path> --write`. See `infrastructure/builder/README.md`
1. **After config changes**: Run `python coverages/doc_generator.py` to regenerate logic.md files
1. **After config changes**: Run calibration harness `python -m layers.risk.calibration_harness <coverage>` to validate pricing

## Implementation Status

All phases through Version 4 are complete. Version 5 is in planning.

**Version history** (detailed phase docs in `development/project/version/`):
- **Version 1** (Phases 1-20): Foundation, signal architecture, coverage implementations, config-driven model, scoring engine, discovery, modifiers, analytics, multi-coverage, production API, integration layer, LLM builder, examples, production extractors
- **Version 2** (R1-R11, P1-P7): Architecture restructuring, production readiness (DB, deployment, observability, performance)
- **Version 3** (V3, Phases A-E): Comprehensive upgrade (foundation/transparency, scoring completeness, ROL engine, config strictness, tower/subscription)
- **Version 4** (Phases 1-13): Multi-configuration multiplexer, coverage expansion pipeline, Phase 6 PI expansion (13 configs), Phase 7 Cyber expansion (11 configs)
- **Version 5** (Phases 1-8): UX conversion (Phase 1), coverage expansion — 3 new coverages (Property, Casualty, FPR) + 4 expansions (Marine, Aerospace, D&O, FI)

**Current coverage configurations (10 coverages, 76 configs):**
| Coverage | Configs | Key Expansion |
|-|-|-|
| Cyber | 11 | Phase 7: 9 industry-specific configs |
| D&O | 6 | V5 Phase 6: public, PE-backed, non-profit, IPO/SPAC |
| FI | 6 | V5 Phase 7: bank, insurer, fintech, crypto |
| Energy | 10 | Phase 5: 8 segment-specific configs |
| Marine | 7 | V5 Phase 3: cargo, tanker, offshore, war risk, high-value |
| PI | 13 | Phase 6: 11 profession-specific configs |
| Aerospace | 7 | V5 Phase 5: space, rotary wing, UAS, MRO, high-value |
| Property | 5 | V5 Phase 2: general, high-value, CAT, builders risk, SME |
| Casualty | 6 | V5 Phase 4: GL, WC, auto, umbrella, environmental, SME |
| FPR | 5 | V5 Phase 8: trade credit, political risk, surety, K&R, SME |

---

## What is DSI?

Digital Signal Intelligence (DSI) is a new insurance information substrate based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

- Foundational Principles: `docs/overview/Foundational Principles.md`
- Whitepaper: `docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf`
- Visionpaper: `docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf`

---

## Architecture Overview

```
SUBMISSION INPUT  -->  DISCOVERY (Step 0)  -->  YAML CONFIG
                                                    |
                                              SIGNAL ARCHITECTURE
                                    (Extractor -> Aggregator -> Categorizer -> Inference)
                                                    |
                          +--------------------------+--------------------------+
                          |                          |                          |
                    RISK SCORING              EXPOSURE SHADOW          LOSS CORRELATION
                   (Steps 5-6)                  (Phase 17)               (Phase 16)
                          |                          |                          |
                          +--------------------------+--------------------------+
                                                    |
                                              PRICING ENGINE
                                    (Risk Tier x Exposure Band x Loss Modifier)
                                                    |
                                              MODEL OUTPUT
                                    (Premium + Decision + Audit Trail)
```

**Four main code areas:**

| Area | Purpose | Key Contents |
|-|-|-|
| `signal_architecture/` | Signal processing | signals, discovery, orchestration, multiplexer, graph |
| `infrastructure/` | Support systems | api, db, analytics, builder, validation, integrations |
| `layers/` | Assessment layers | risk (14-step workflow), exposure, loss |
| `coverages/` | Configuration | YAML configs for all 10 coverages + doc_generator |

**Additional areas:**
- `commercial/entities/` - Commercial entity definitions (distribution, commission, FX)
- `deploy/` - Docker, Kubernetes, monitoring configs
- `rust/dsi-core/` - PyO3 performance crate (PageRank, derivatives)
- `frontend/` - Next.js React workbench UI

---

## YAML Config Structure

**CRITICAL: The YAML config is the single source of truth. Never hardcode values that exist in config.**

**Reference:** `coverages/master_config_layout.yaml` - VERSION 2.3

Each coverage line has a single `config.yaml` containing one or more sub-configurations:

```yaml
coverage:                          # Domain (e.g., cyber, pi)
  configuration:                   # Instantiable model (e.g., cyber_healthcare)
    metadata:                      # Name, version, min premium, routing_constraints
    direct_queries:                # Boolean questions (Step 7) with conditions
    signal_registry:               # All signals with three_layer_assessment weights
    groups:
      categories:                  # Categorical modifier groups
      three_layer_assessment:      # Score-contributing groups with per-layer weights
    risk_tier_bands:               # Score -> tier -> premium (5 tiers)
    loss_tier_bands:               # Loss score -> frequency/severity modifiers
    exposure:                      # Exposure score -> size/complexity modifiers
    limit_configuration:           # DECOUPLED | BUNDLED | TOWER | SUBSCRIPTION
    pricing:                       # ILF curves (parametric), deductible factors
    guardrails:                    # Modifier caps, premium-to-limit ratio limits
```

For full schema details, see `coverages/master_config_layout.yaml`.

---

## Critical Rules

### Core Framework

1. **YAML is truth**: Never hardcode weights, thresholds, modifiers, or tier definitions
1. **Parametric ILF only**: All ILF curves must use `anchor_limit`/`curve`/`params` format
1. **Scores are 0-100**: Individual signals; **Composite is 0-1000**: Weighted sum x 10
1. **Auditability**: Every price must trace back to signals -> scores -> tier -> premium
1. **Three layers run in parallel**: Risk, Exposure, Loss - same signals, different weights
1. **Pricing uses all three outputs**: Risk Tier x Exposure Band x Loss Modifier -> Premium
1. **Maximum tier override wins**: When multiple overrides, apply worst tier

### score_conditions Rules

1. **Applies to:** signal_registry signals and groups ONLY (NOT tier bands)
1. **MODIFIER:** ALL matching conditions apply multiplicatively
1. **FLAG:** ALL matching conditions captured
1. **REFER:** FIRST matching triggers referral
1. **Required fields:** MODIFIER needs `applied`, FLAG needs `note`, REFER optionally takes `override`

### Coverage Expansion Pipeline

When expanding a coverage line with new sub-configurations:

1. **Author** expansion spec YAML (see `development/project/version/4/phase_6_spec.yaml`)
2. **Dry-run**: `python -m infrastructure.builder.cli expand --spec <path> --dry-run`
3. **Execute**: `python -m infrastructure.builder.cli expand --spec <path> --existing-config coverages/<cov>/config.yaml --write`
4. **Calibrate**: `python -m layers.risk.calibration_harness <coverage>` - all configs must pass (<15% guardrail hit rate)
5. **Regenerate docs**: `python coverages/doc_generator.py`
6. **Update seed script**: Add company entries and signal profiles to `seed_dsi_bench.py`

Spec schema: `infrastructure/builder/expansion_types.py`
Generator: `infrastructure/builder/expansion_generator.py`
Full docs: `infrastructure/builder/README.md`

### Commercial Terms & Risk Terms

Commercial entity economics (FX, commission, taxes, distribution) are defined in `commercial/entities/` as YAML files. The `PremiumAssembler` (`layers/risk/premium_assembly.py`) transforms technical premium into gross/offered premium.

DB tables: `commercial_terms` and `risk_terms` (migration 007).
Schema: `infrastructure/models/commercial_schema.py`
API routes: `infrastructure/api/routes/commercial.py`

---

## Key Reference Documents

| Document | Location | Purpose |
|-|-|-|
| Foundational Principles | `docs/overview/Foundational Principles.md` | Core DSI principles (must follow) |
| Config Schema | `coverages/master_config_layout.yaml` | YAML config structure reference |
| Builder README | `infrastructure/builder/README.md` | Coverage expansion pipeline docs |
| Extractor Plan | `development/extractor_implementation_plan.md` | Stub-to-production conversion roadmap |
| Coverage Logic | `coverages/<cov>/logic.md` | Auto-generated config documentation |
| Phase Plans | `development/project/version/` | Detailed phase development docs |

---

## Seed Script

`seed_dsi_bench.py` seeds the database with realistic end-to-end data covering every coverage, configuration, tier, and decision path. Uses production workflow components (ModelScorer, ModelPricer, QueryEvaluator) for all calculations.

Run: `python seed_dsi_bench.py`
