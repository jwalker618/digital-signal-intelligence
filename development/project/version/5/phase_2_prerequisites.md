# Version 5 Phase 2: Coverage Expansion Prerequisites

## Overview

Before executing any coverage expansion spec, a set of infrastructure
touchpoints must be addressed. This document catalogues every file and
registration point that must be updated when adding a **new** coverage line
or **expanding** an existing one, and identifies potential issues with
methodology, calibration, and volume that should be resolved first.

---

## 1. Infrastructure Touchpoints

### 1a. New Coverage Line (Property, Casualty, Financial & Political Risk)

Each new coverage requires changes in **5 locations** before the builder
output will compile, seed, and pass the health gate.

| # | File / Location | Change Required |
|---|-----------------|-----------------|
| 1 | `coverages/{coverage}/config.yaml` | Created by builder from spec |
| 2 | `coverages/{coverage}/__init__.py` | Empty file — created by builder |
| 3 | `signal_architecture/signals/inference/metadata_registry.py` | Add constant (`COVERAGE_PROPERTY = "property"`), add to `ALL_COVERAGES` list (line 65), create `_PROPERTY_SIGNALS` list, call `SIGNAL_METADATA_REGISTRY.register_many()` |
| 4 | `seed_dsi_bench.py` | Add entry to `COVERAGE_ENTITY_MAP` (line ~4034), update docstring (line ~13) |
| 5 | `commercial/entities/{entity}.yaml` | Either create new entity or add `CoverageBinding` to existing entity |

**Automatically handled (no manual work):**
- Config compiler — scans `coverages/` via `iterdir()`
- Config health gate — auto-tests all discovered configs
- Config validator — auto-validates all discovered configs
- Calibration harness — auto-generates fixtures for all configs
- Signal broker/multiplexer — loads configs dynamically

### 1b. Expanded Coverage Line (Aerospace, D&O, FI, Marine)

Expansion adds configurations to an **existing** `config.yaml`. Fewer
touchpoints because the coverage directory and registry entry already exist.

| # | File / Location | Change Required |
|---|-----------------|-----------------|
| 1 | `coverages/{coverage}/config.yaml` | Updated by builder — new configs appended |
| 2 | `signal_architecture/signals/inference/metadata_registry.py` | Only if new signals are introduced — add to existing `_{COVERAGE}_SIGNALS` list |
| 3 | `seed_dsi_bench.py` | Update docstring to list new config IDs; existing entity mapping may suffice |

---

## 2. Methodology Risks

### 2a. Variable Basis Fields Within a Single Coverage

**Affected:** Casualty, Financial & Political Risk

Casualty sub-lines use different premium bases:
- General Liability → revenue
- Workers Compensation → payroll
- Commercial Auto → fleet_value / vehicle_count
- Umbrella/Excess → underlying_premium

The multiplexer and pricing engine support per-config `basis` fields in
`risk_tier_bands`, so each configuration can declare its own basis. However:

**Risk:** `minimum_viable_input` is currently shared across all configs in a
coverage. If one config requires `payroll` and another requires `fleet_value`,
both must appear in the coverage-level minimum input, but only one is relevant
per submission. The multiplexer's `routing_constraints` must filter correctly
so that a GL submission never reaches the auto liability config.

**Mitigation:** Use `required_in_input: true` on routing constraints to ensure
the basis field is present before a config can be selected. Validate that
routing constraints are mutually exclusive across configs within a coverage.

### 2b. TIV vs Limit as Basis

**Affected:** Property

Property pricing is TIV-based (rate × total insured value), but loss limits
are separate from TIV. The existing `master_config_layout.yaml` supports
`basis: tiv` in risk tier bands (line 446-448). Marine already uses this
pattern (`basis: tiv`), confirming it works end-to-end.

**No blocking issue** — follow the marine precedent.

### 2c. Occurrence vs Claims-Made Trigger

**Affected:** Property (occurrence), Casualty (occurrence), vs existing
PI/D&O/Cyber (claims-made)

The pricing engine does not currently differentiate between occurrence and
claims-made policy triggers. For Property and Casualty this matters because:
- No retroactive date / prior acts considerations
- IBNR patterns differ significantly
- Loss development tails are shorter

**Mitigation:** This is a **metadata/documentation concern** only at the spec
level. The pricing engine calculates technical premium identically regardless
of trigger. Flag as a future enhancement if actuarial loss development
modelling is added.

### 2d. Catastrophe Accumulation (CAT Exposure)

**Affected:** Property (primary), Marine (secondary), Aerospace (tertiary)

Property is heavily CAT-exposed (hurricane, earthquake, flood, wildfire).
The current signal architecture handles this via scored signals contributing
to the exposure dimension, but there is no **aggregate accumulation** tracking
across the book.

**Mitigation:** CAT exposure signals can flag individual risk quality. Book-
level accumulation is outside the scope of per-risk pricing and should be
tracked at the portfolio management layer, not in the coverage config. No
blocking issue for spec creation.

### 2e. Excess/Surplus Lines vs Admitted

**Affected:** Property, Casualty

US property and casualty markets distinguish between admitted (rate-filed)
and E&S (surplus lines) business. Rate flexibility differs significantly.

**Mitigation:** Handle via `routing_constraints` — an `admitted` boolean field
can route to configs with tighter guardrails (lower modifier caps, filed
rates). E&S configs get wider guardrails. This is a config-level concern,
not a methodology issue.

---

## 3. Calibration Risks

### 3a. Rate Level Validation

Each new/expanded coverage needs realistic base rates. Sources:

| Coverage | Basis | Typical Rate Range | Reference |
|----------|-------|-------------------|-----------|
| Property | TIV | 0.05% - 0.50% | ISO/AAIS commercial fire rates |
| Casualty GL | Revenue | 0.10% - 1.50% | ISO CGL by class code |
| Casualty WC | Payroll | 0.50% - 15.00% | NCCI manual rates (class dependent) |
| Casualty Auto | Fleet Value | 1.00% - 5.00% | Commercial auto manual |
| Marine (expanded) | TIV/Hull | 0.10% - 0.80% | Lloyd's market rates |
| Aerospace (expanded) | Hull Value | 0.08% - 0.60% | London aviation market |
| D&O (expanded) | Revenue | 0.003% - 0.10% | Existing config validates |
| FI (expanded) | Total Assets | 0.0005% - 0.005% | Existing config validates |
| FPR Trade Credit | Contract Value | 0.20% - 3.00% | Berne Union rates |
| FPR Political Risk | Limit | 0.50% - 5.00% | Specialty market |

**Risk:** Setting rates too low results in health gate failures (premium-to-
limit ratio too low). Setting rates too high triggers the `max_premium_to_
limit_ratio` guardrail (default 0.35).

**Mitigation:** Each spec must define rates within the guardrail corridor.
The health gate auto-tests all tier/product/limit combinations — failures
surface immediately.

### 3b. ILF Curve Shape

Property and Casualty ILF curves are **flatter** than liability lines because
loss severity is more bounded (by TIV). A $10M property loss on a $100M TIV
risk is common; a $10M PI loss on a $5M revenue firm is catastrophic.

**Mitigation:** Property ILF factors should be lower than PI equivalents at
each limit point. Use ISO/Lloyd's published ILF tables as reference anchors.

### 3c. Expanded Config Volume

Current state: 7 coverages × ~2 configs each = ~14 active configs.
After expansion: ~10 coverages × ~5 configs average = ~50 active configs.

**Risks:**
- Calibration harness runtime increases ~3.5x
- Multiplexer fan-out increases per submission
- Seed data volume increases substantially

**Mitigation:** None of these are blocking. The calibration harness and
multiplexer are designed for this scale. Monitor test execution time.

---

## 4. Signal Volume & Reuse

### 4a. Cross-Coverage Signal Opportunities

Several signal groups are reusable across new coverages:

| Existing Group | Currently Used By | Applicable To |
|---------------|-------------------|---------------|
| `corporate_footprint` | All | Property, Casualty, FPR |
| `network_authority` | All | Property, Casualty |
| `regulatory_standing` | All | Property, Casualty, FPR |
| `firm_stability` | All | Property, Casualty |
| `litigation_history` | PI, D&O | Casualty, FPR |
| `technical_infrastructure` | All | Property (fire protection systems) |

**Benefit:** Reusing existing groups reduces signal count and leverages
already-calibrated weights. New groups should only be created for genuinely
coverage-specific risk factors.

### 4b. New Signal Group Estimates

| Coverage | Estimated New Groups | Estimated New Signals | Rationale |
|----------|---------------------|----------------------|-----------|
| Property | 4-5 | 25-35 | Construction, occupancy, protection, CAT exposure, BI |
| Marine (expand) | 3-4 | 20-25 | Cargo type, tanker-specific, offshore, port state |
| Casualty | 5-7 | 35-50 | GL class, WC class, auto fleet, umbrella, environmental |
| Aerospace (expand) | 3-4 | 18-25 | Space, MRO, rotary wing, unmanned |
| D&O (expand) | 2-3 | 12-18 | Public company, PE-backed, IPO/SPAC |
| FI (expand) | 2-3 | 12-18 | Bank-specific, insurer, fintech/crypto |
| FPR | 4-5 | 25-35 | Trade credit, political violence, surety, K&R |

**Total estimated new signals: ~150-200**
**Total estimated new groups: ~25-30**

---

## 5. Execution Sequence & Dependencies

```
Phase 2: Property Spec          ← New coverage, clean slate, no dependencies
    |
Phase 3: Marine Expansion       ← Builds on existing marine config
    |
Phase 4: Casualty Spec          ← New coverage, variable basis (most complex)
    |
Phase 5: Aerospace Expansion    ← Builds on existing aerospace config
    |
Phase 6: D&O Expansion          ← Builds on existing do config
    |
Phase 7: FI Expansion           ← Builds on existing fi config
    |
Phase 8: FPR Spec               ← New coverage, most niche, least urgent
```

**Why this order:**
1. Property is the most standard commercial coverage — establishes the pattern
   for TIV-based, occurrence-trigger configs
2. Marine expansion reuses the TIV basis established in Property
3. Casualty is the most complex (variable basis) — benefits from Property
   and Marine learnings
4. Aerospace/D&O/FI expansions are lower risk — existing base configs proven
5. FPR is the most niche and least urgent — benefits from all prior work

---

## 6. Per-Spec Deliverable Checklist

Each phase spec must include:

- [ ] Header metadata (coverage_line, coverage_key, phase, version)
- [ ] Default product types and markets
- [ ] Default minimum viable input (including basis field)
- [ ] Default tier bands (risk, loss, exposure) with realistic rates
- [ ] Default ILF curves and deductible factors per product type
- [ ] New signal groups with fully defined signals
- [ ] Configurations with routing constraints, group weights, direct queries
- [ ] Per-config pricing overrides where needed
- [ ] Per-config limit/deductible menus
- [ ] Infrastructure touchpoint notes (for new coverages only)

---

## 7. Pre-Execution Validation

Before any spec is fed to the builder, verify:

1. **YAML syntax** — `python -c "import yaml; yaml.safe_load(open('spec.yaml'))"`
2. **Weight sums** — group_weights for each config sum to ~1.0 per dimension
3. **Routing exclusivity** — no two configs within a coverage match the same
   routing constraint set
4. **Basis field present** — the `basis` field in risk_tier_bands matches a
   field in minimum_viable_input
5. **Rate corridor** — rates fall within guardrail bounds (min_premium to
   max_premium_to_limit_ratio)
6. **ILF monotonicity** — ILF factors increase with limit
7. **Deductible monotonicity** — deductible factors decrease with deductible
