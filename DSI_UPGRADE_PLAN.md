# DSI Comprehensive Upgrade Plan

## Investigation Findings & Implementation Roadmap

---

## FINDINGS SUMMARY

### 1. ILF Application Chain — Not Transparent

**Problem**: Cannot see how ILF transforms premium. Example: `premium_after_modifiers = $2.15M`, `ILF = 3.3`, but `final_premium = $4,921,542` — the math isn't visible.

**Root Cause**: `scale_to_limits()` in `pricer.py` (line 500-502) calculates `limit_premium = premium * ilf * ded_factor` but only stores the final `limit_premiums: Dict[str, float]` — a flat dict with no breakdown.

**What's missing**:
- Per-limit ILF factor used
- Per-limit deductible factor used
- Pre-ILF premium (premium_after_modifiers) not carried through to limit-level output
- No audit trail showing: `base × modifiers × ILF × ded_factor = final`

**Fix**: Replace `limit_premiums: Dict[str, float]` with a structured `LimitPremiumDetail` per limit showing each component. Must store `ilf_factor` and `deductible_factor` as discrete fields (not just the computed result) to support future layer pricing via `ILF(attachment + limit) - ILF(attachment)`.

---

### 2. Loss/Exposure Modifiers — Applied But Contradictory Display Values

**Finding**: Both modifiers DO reach the pricer and affect final premium. However, the **displayed values contradict the actual pricing values**.

**Critical bug — dual exposure systems producing opposite results**:
- **Display path** (`workflow.py` ~line 556): `_EXPOSURE_BANDS` metadata table maps revenue bands to display modifiers. JPMorgan ($160B) → Mega band → **display shows `exposure_modifier: 1.30`** (a loading)
- **Pricing path** (`modifiers/exposure.py`): `SIZE_CURVE_ISO_2` ISO curve maps revenue to actual pricing factor. JPMorgan ($160B) → top bucket → **actual pricing applies `factor: 0.70`** (a credit)

These are two completely disconnected lookup tables producing opposite directional impacts. The user sees "1.3x exposure loading" but the premium is actually multiplied by 0.70x. This is genuinely misleading, not just a visibility issue.

**Fix**: Eliminate the dual-system disconnect. The display/metadata values must reflect what's actually used in pricing. Remove or replace the `_EXPOSURE_BANDS` display table so `model_version.exposure_modifier` matches the factor that enters the pricing chain.

---

### 3. Loss Score Fields — Semantics Unclear

**Finding**: In `LossPropensityResult`:
- `previous_score` = prior period's combined loss propensity score (not frequency or severity individually)
- `score_velocity` = rate of change between periods (positive = worsening)
- Both relate to the **combined** loss propensity, not individual frequency/severity

**Problem**: Field names don't communicate this. No individual frequency/severity trend tracking.

**Fix**: Rename fields for clarity, add frequency/severity individual trend fields.

---

### 4. Exposure Detail — Dual Systems, Opaque Output

**Finding**: Two parallel exposure systems exist:
1. **Signal-driven** (config bands): Signals score 0-100 → mapped to config exposure bands (size/complexity) → weighted into group scores
2. **Submission-driven** (traditional modifier): TIV/revenue → ISO curve lookup → separate hardcoded bands

**What's lost**:
- Individual signal contributions to exposure dimensions (aggregated in group scores)
- Component factors from full-mode assessment (growth, concentration, employee intensity)
- Magnitude vs complexity split (merged into single score)
- Config-defined exposure bands vs actual modifier bands are disconnected

**Fix**: Surface exposure dimension breakdown (magnitude + complexity scores separately), persist component factors, align config bands with modifier bands.

---

### 5. Score Conditions — Only Evaluated for Risk

**Finding**: CONFIRMED GAP.
- Schema supports `score_conditions` on all three dimensions: risk, loss, exposure
- Config files DEFINE loss score_conditions (e.g., cyber config has modifier conditions on loss groups)
- `evaluate_signal_conditions()` in `scorer.py` lines 722-783 ONLY evaluates `risk.score_conditions`
- **Loss and exposure score_conditions are silently ignored**

**Fix**: Extend `evaluate_signal_conditions()` to evaluate loss and exposure dimension conditions.

---

### 6. Tier Band Marginal Context — Not Provided

**Finding**: Tier assignment is a binary range check (`min <= score <= max`). No proximity/margin data exists:
- No "distance to next tier" calculation
- No "percentile within tier"
- No "barely Tier 3" context for underwriter review

**Fix**: Add `tier_margin` context to PricingResult: distance to adjacent tier boundaries, percentile within current tier.

---

### 7. Config Detail Underutilization

**Finding**: Config YAML contains rich detail (signal weights per dimension, exposure implied_thresholds, tier band descriptions, score_conditions) that doesn't surface in output. The config is well-structured but the workflow only extracts what it needs for pricing, discarding context valuable for underwriter decisions.

**Fix**: This is addressed by fixes #2 (exposure alignment), #4 (exposure detail), #5 (score_conditions), #6 (tier context). No separate work item needed.

---

### 8. Config Builder Too Permissive + Configs Not Cleaned Up

**Finding**:
- Pydantic models use default `extra="ignore"` — unknown YAML fields silently dropped
- `ComparisonOperator` accepts aliases (`=` and `==`)
- No cross-coverage field naming consistency validation
- Builder generates valid YAML but validator doesn't reject extra fields
- **Existing config files have not been cleaned up** to remove accumulated permissiveness artifacts

**Fix**: Add `model_config = ConfigDict(extra="forbid")` to key schema classes. Audit and standardize comparison operators. **Clean up all existing config YAML files** to pass strict validation.

---

### 9. Uncapped Premium — Not Captured

**Finding**: CONFIRMED.
- Guardrail capping in `pricer.py` lines 141-174 overwrites `final_premium` in place
- Only `premium_was_capped: bool` is stored
- Pre-cap value exists only transiently and is lost
- Not stored in database (`ModelVersionRecord` has no uncapped column)

**Fix**: Add `uncapped_premium: Optional[float]` to PricingResult and ModelVersion. Populate before guardrail application.

---

### 10. ROL-Based Validation & Dual Recommendations

**Current state**: `PremiumValidator` checks P/L ratios per limit cohort. Limit recommendation is simply the median of the option menu (no economic logic).

**Required**:
- ROL curve validator replaces PremiumValidator
- Dual recommendation engine (upper/lower ROL-optimal limits)
- Ability to re-price with different limit selection
- ConfigHealthGate updated to use ROL validator

---

### 11. Tower/Subscription Market Support

**Finding**: ZERO support currently.
- Single limit pricing only (BUNDLED or DECOUPLED options)
- No attachment points, layers, or stacking
- No subscription/syndication participation percentages
- No excess-of-loss layer pricing

**Key architectural insight**: Existing ILF curves are cumulative ground-up curves. Tower layer pricing derives mathematically: `Premium(layer X xs Y) = Premium(X+Y) - Premium(Y)`. The ILF curves themselves don't change — you evaluate at two points and subtract. This means Phases A-C can proceed safely if we make small design accommodations now (see Phase E Design Accommodations below).

**Required**:
- Tower layer definitions in config schema
- Layer-specific attachment-based pricing (derived from existing ILF curves)
- Subscription participation percentage handling
- Multi-layer pricing output

---

### 12. Remove Table-Based ILF

**Finding**: ILFCurve supports both parametric (5 curve types) and legacy table (base_limit + factors list). Table should be removed — parametric is the standard.

---

### 13. Builder Phase 6/7 Execution — Not Done

**Finding**: The expansion builder tooling is fully built and ready, but:
- **Phase 6** (PI expansion, 11 configs): Complete YAML spec exists (`phase_6_spec.yaml`) but **never executed**. PI config still only has `pi_general` + `pi_sme`.
- **Phase 7** (Cyber expansion, 10 configs): **No spec YAML exists** — only a prose companion doc (`phase_7.md`). Cyber config still only has `cyber_general` + `cyber_sme`.

**Required**:
- Author `phase_7_spec.yaml` from the existing prose doc
- Execute Phase 6 expansion against PI config
- Execute Phase 7 expansion against Cyber config
- Validate expanded configs pass health gate and seed bench

---

## IMPLEMENTATION PHASES

### Phase A: Foundation & Transparency (Do First)
*These are prerequisite fixes that make everything else measurable.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| A1 | **Capture uncapped premium** — add `uncapped_premium: Optional[float]` to PricingResult, ModelVersion, and DB schema. Populate before guardrail capping | pricer.py, types.py, db/models.py | Small |
| A2 | **ILF transparency** — structured `LimitPremiumDetail` replacing flat dict. Must store `ilf_factor` and `deductible_factor` as discrete component fields (not just computed premium) to enable future layer pricing composition | pricer.py, types.py | Medium |
| A3 | **Modifier visibility + exposure alignment** — categorize modifiers by type (signal, loss, exposure, traditional) with before/after premium per modifier. **Fix the dual-exposure disconnect**: eliminate `_EXPOSURE_BANDS` display table so displayed values match actual pricing factors | pricer.py, types.py, workflow.py | Medium |
| A4 | **Tier margin context** — distance to boundaries, percentile in tier | pricer.py, types.py, config_schema.py | Small |
| A5 | **Remove table-based ILF** — enforce parametric-only in schema, remove table support from ILFCurve, update any configs/tests using table ILF | config_schema.py, pricer.py, config YAMLs | Medium |
| A6 | **Phase A tests** — unit tests for uncapped premium capture, ILF transparency output (including component field storage), modifier categorization, tier margin calculations. Update existing tests that use table-based ILF | tests/unit/test_pricer.py, tests/unit/test_config_health_gate.py | Medium |

### Phase B: Scoring Completeness
*Wire up capabilities that exist in schema but aren't executing.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| B1 | **Evaluate loss/exposure score_conditions** — extend `evaluate_signal_conditions()` to process loss and exposure dimension conditions, not just risk | scorer.py, workflow.py | Medium |
| B2 | **Surface exposure dimension breakdown** — persist magnitude vs complexity scores separately, component factors (growth, concentration), align config bands with modifier output | workflow.py, types.py, exposure/scorer.py | Medium |
| B3 | **Clarify loss score fields** — rename for clarity, add individual frequency/severity trend fields | loss/types.py, workflow.py | Small |
| B4 | **Phase B tests** — unit tests for loss/exposure score_conditions evaluation, exposure dimension breakdown output, loss field clarity | tests/unit/test_scorer.py, tests/unit/test_workflow.py | Medium |

### Phase C: ROL Engine (Core Upgrade)
*Replaces PremiumValidator and limit recommendation logic entirely.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| C1 | **Build ROL curve validator** — replaces PremiumValidator entirely. Per-coverage ROL appetite bands. Core signature: `validate_rol(premium, limit, attachment=0)` with bands keyed by `(attachment_range, limit_range)` to support future tower pricing without redesign | NEW: layers/risk/rol_validator.py | Large |
| C2 | **ROL dual recommendation engine** — replaces the median-of-menu limit selection. Produces upper recommendation (best value higher limit with attractive ROL) and lower recommendation (minimum adequate at client's request). Output includes `attachment: float = 0`, `participation_pct: float = 1.0`, `structure_type: str = "ground_up"` fields from day one for future tower/subscription compatibility | NEW: layers/risk/rol_recommender.py | Large |
| C3 | **Limit re-calculation method** — ability to reprice with a different limit selection without re-running entire workflow | workflow.py, pricer.py | Medium |
| C4 | **Update ConfigHealthGate** to use ROL validator instead of PremiumValidator for boot-time config validation | config_health_gate.py | Medium |
| C5 | **Remove PremiumValidator** — fully replaced by ROL validator, not alongside it | premium_validator.py (delete), workflow.py | Small |
| C6 | **ROL engine tests** — unit tests for ROL validator, dual recommender, re-calculation, and ConfigHealthGate ROL integration | NEW: tests/unit/test_rol_validator.py, tests/unit/test_rol_recommender.py | Large |

### Phase D: Config Strictness & Cleanup
*Tighten validation and clean up existing configs.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| D1 | **Add extra="forbid" to schema models** — reject unknown YAML fields | config_schema.py | Medium |
| D2 | **Standardize comparison operators** — remove aliases, enforce single canonical form | config_schema.py, configs | Small |
| D3 | **Cross-coverage field consistency validation** | builder/validator.py | Medium |
| D4 | **Clean up existing config YAML files** — audit all coverage configs against strict schema, remove extraneous fields, fix inconsistencies, ensure all pass `extra="forbid"` validation | coverages/*/config.yaml | Medium |

### Phase E: Market Structure
*Major architectural addition for tower/subscription markets. Requires design review before implementation.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| E1 | **Phase E design review** — detailed design document for tower/subscription covering: layer schema, attachment-based ILF derivation, subscription participation model, multi-layer output types, API contract changes, config builder extensions. Must be reviewed before E2-E5 | NEW: development/project/phase_e_design.md | Medium |
| E2 | **Tower layer schema** — add `TOWER` type to LimitConfiguration with layer definitions (attachment, limit, per-layer ILF evaluation points). Extend `generate_limit_options()` to be polymorphic for ground-up vs tower | config_schema.py | Large |
| E3 | **Multi-layer pricing engine** — tower pricing via `ILF(attachment + limit) - ILF(attachment)` derivation from existing cumulative curves. Per-layer premium, per-layer uncapped premium, per-layer ROL | pricer.py, workflow.py | Large |
| E4 | **Subscription participation** — add `SUBSCRIPTION` type with `total_limit`, `participation_pct`, `minimum_line`, `maximum_line`. Premium = participation% × full_premium. ROL unchanged (applies to whole) | config_schema.py, pricer.py | Large |
| E5 | **Tower/subscription output types** — `LayerPremiumDetail` composing two `LimitPremiumDetail` evaluations, multi-layer recommendation output | types.py | Medium |

### Phase F: Builder Execution & Config Expansion
*Execute pending expansion phases and ensure configs are production-ready. Should run after D (strict schema) to ensure expanded configs meet new standards.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| F1 | **Author phase_7_spec.yaml** — convert existing `phase_7.md` prose doc into machine-consumable expansion spec YAML, matching the format of `phase_6_spec.yaml` | NEW: development/project/version/4/phase_7_spec.yaml | Medium |
| F2 | **Execute Phase 6 expansion** — run `cli expand` with `phase_6_spec.yaml` against PI config, generating 11 new sub-configurations, extractor stubs, aggregator stubs | coverages/pi/config.yaml, coverages/pi/extractors/, coverages/pi/aggregators/ | Medium |
| F3 | **Execute Phase 7 expansion** — run `cli expand` with `phase_7_spec.yaml` against Cyber config, generating 10 new sub-configurations | coverages/cyber/config.yaml, coverages/cyber/extractors/, coverages/cyber/aggregators/ | Medium |
| F4 | **Validate expanded configs** — all expanded configs pass ConfigHealthGate, ROL validator, strict schema validation, and seed bench | All coverage configs | Medium |
| F5 | **Phase F tests** — seed bench expansion to cover new sub-configurations, verify routing works for profession/industry segments | seed_dsi_bench.py, tests/ | Medium |

---

## PHASE E DESIGN ACCOMMODATIONS (Built Into A-C)

These small design decisions are built into Phases A-C to avoid rework when Phase E arrives:

| Phase | Item | Accommodation | Impact on Ground-Up Behavior |
|-------|------|---------------|-------------------------------|
| A2 | LimitPremiumDetail | Store `ilf_factor` and `deductible_factor` as discrete fields, not just computed premium | None — same data, more granular |
| C1 | ROL Validator | Signature: `validate_rol(premium, limit, attachment=0)`. Bands keyed by `(attachment_range, limit_range)` | None — `attachment=0` default |
| C2 | Dual Recommender | Output includes `attachment: float = 0`, `participation_pct: float = 1.0`, `structure_type: str = "ground_up"` | None — defaults match current behavior |

**Key insight**: ILF curves are cumulative. Tower layer pricing = `ILF(attachment + limit) - ILF(attachment)`. The parametric curves don't change — Phase E composes existing evaluations, not new curve types.

---

## EXECUTION ORDER

```
Phase A (Foundation)  ──→  Phase C (ROL Engine)  ──→  Phase E (Market Structure)
                                │
Phase B (Scoring) ──────────────┤
                                │
                                ├──→  Phase D (Config Strictness)  ──→  Phase F (Builder Execution)
```

**Phases A and B** can be developed concurrently — no dependencies.
**Phase C** depends on A1 (uncapped premium) and A2 (ILF transparency).
**Phase D** can run in parallel with C.
**Phase E** depends on C (ROL engine) being stable. Requires E1 design review before implementation.
**Phase F** depends on D (strict schema) to ensure expanded configs meet new standards.

---

## TESTING STRATEGY

Each phase includes explicit test work items (A6, B4, C6, F5). In addition:

- **Seed bench re-run**: `seed_dsi_bench.py` (61 companies) must be re-run after each phase to verify no regressions and validate new output fields
- **ConfigHealthGate**: All production configs must continue passing health checks throughout — this is a continuous gate
- **Existing test suite**: All existing unit tests must pass after each phase; test fixtures using table-based ILF must be migrated in Phase A
- **ROL validation**: Phase C requires new integration tests that verify ROL validator produces sensible results across all production configs (replaces the PremiumValidator coverage)
- **Regression test**: After PremiumValidator removal (C5), verify that all previously-passing submissions still price correctly under the ROL regime

## NOTES

- Frontend components (PricingTab, RiskTab, etc.) will need updates after Phase A to display new detail fields (ILF breakdown, uncapped premium, tier margins)
- ROL appetite bands per coverage will need calibration — this is a configuration exercise alongside the code work in Phase C
- The ROL engine replaces PremiumValidator **entirely** — it is not a parallel system running alongside it
- Phase E requires a dedicated design review (E1) before any implementation begins — the ramifications of tower/subscription on the entire pipeline must be fully considered
- Phase F should not execute until Phase D's strict schema is in place, otherwise expanded configs may introduce the same permissiveness issues we're cleaning up
