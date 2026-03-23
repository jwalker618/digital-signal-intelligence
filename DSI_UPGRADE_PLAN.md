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

**Fix**: Replace `limit_premiums: Dict[str, float]` with a structured `LimitPremiumDetail` per limit showing each component.

---

### 2. Loss/Exposure Modifiers — ARE Applied (But Not Visible)

**Finding**: Both modifiers ARE reaching the pricer and affecting final premium.

- **Loss modifier**: Added to `all_modifiers` at `workflow.py` line 412-418 as `{"name": "loss_propensity", "factor": combined_loss_modifier}`
- **Exposure modifier**: Converted via `traditional_modifiers_for_pricer` at `workflow.py` line 402-406, filtered by `has_impact`

**The real problem**: The effect is invisible because `modifiers_applied` in PricingResult is a flat list. Users can't easily see which modifiers actually changed the premium and by how much. The modifier names are technical ("loss_propensity", "exposure") without context.

**Fix**: Enhance modifier output with before/after premium per modifier, categorize modifiers by type (signal, loss, exposure, traditional).

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

**Fix**: This is addressed by fixes #4 (exposure detail), #5 (score_conditions), #6 (tier context). No separate work item needed.

---

### 8. Config Builder Too Permissive

**Finding**:
- Pydantic models use default `extra="ignore"` — unknown YAML fields silently dropped
- `ComparisonOperator` accepts aliases (`=` and `==`)
- No cross-coverage field naming consistency validation
- Builder generates valid YAML but validator doesn't reject extra fields

**Fix**: Add `model_config = ConfigDict(extra="forbid")` to key schema classes. Audit and standardize comparison operators.

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

**Required**:
- Tower layer definitions in config schema
- Layer-specific ILF curves and attachment-based pricing
- Subscription participation percentage handling
- Multi-layer pricing output

---

### 12. Remove Table-Based ILF

**Finding**: ILFCurve supports both parametric (5 curve types) and legacy table (base_limit + factors list). Table should be removed — parametric is the standard.

---

## IMPLEMENTATION PHASES

### Phase A: Foundation & Transparency (Do First)
*These are prerequisite fixes that make everything else measurable.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| A1 | **Capture uncapped premium** | pricer.py, types.py, db/models.py | Small |
| A2 | **ILF transparency** — structured LimitPremiumDetail replacing flat dict | pricer.py, types.py | Medium |
| A3 | **Modifier visibility** — categorize and show before/after per modifier | pricer.py, types.py, workflow.py | Medium |
| A4 | **Tier margin context** — distance to boundaries, percentile in tier | pricer.py, types.py, config_schema.py | Small |
| A5 | **Remove table-based ILF** — parametric only | config_schema.py, pricer.py, tests | Medium |

### Phase B: Scoring Completeness
*Wire up capabilities that exist in schema but aren't executing.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| B1 | **Evaluate loss/exposure score_conditions** | scorer.py, workflow.py | Medium |
| B2 | **Surface exposure dimension breakdown** | workflow.py, types.py, exposure/scorer.py | Medium |
| B3 | **Clarify loss score fields** — rename, add individual trends | loss/types.py, workflow.py | Small |

### Phase C: ROL Engine (Core Upgrade)
*Replaces PremiumValidator and limit recommendation logic.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| C1 | **Build ROL curve validator** — replaces PremiumValidator | NEW: layers/risk/rol_validator.py | Large |
| C2 | **ROL dual recommendation engine** — upper/lower optimal limits | NEW: layers/risk/rol_recommender.py | Large |
| C3 | **Limit re-calculation method** — reprice with different limit | workflow.py, pricer.py | Medium |
| C4 | **Update ConfigHealthGate** to use ROL validator | config_health_gate.py | Medium |
| C5 | **Remove PremiumValidator** — replaced by ROL | premium_validator.py (delete) | Small |

### Phase D: Config Strictness
*Tighten validation to prevent misconfiguration.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| D1 | **Add extra="forbid" to schema models** | config_schema.py | Medium |
| D2 | **Standardize comparison operators** — remove aliases | config_schema.py, configs | Small |
| D3 | **Cross-coverage field consistency validation** | builder/validator.py | Medium |

### Phase E: Market Structure (Future)
*Major architectural addition for tower/subscription markets.*

| # | Item | Files | Effort |
|---|------|-------|--------|
| E1 | **Tower layer schema** — layer definitions, attachment points | config_schema.py | Large |
| E2 | **Multi-layer pricing engine** | pricer.py, workflow.py | Large |
| E3 | **Subscription participation** — line of whole, percentage | config_schema.py, pricer.py | Large |
| E4 | **Tower/subscription output types** | types.py | Medium |

---

## EXECUTION ORDER

```
Phase A (Foundation)  ──→  Phase B (Scoring)  ──→  Phase C (ROL Engine)
                                                         │
                                                         ├──→  Phase D (Config Strictness)
                                                         │
                                                         └──→  Phase E (Market Structure)
```

**Phases A and B** can be developed concurrently — no dependencies.
**Phase C** depends on A1 (uncapped premium) and A2 (ILF transparency).
**Phase D** can run in parallel with C once B is complete.
**Phase E** depends on C (ROL engine) being stable.

---

## NOTES

- All seed bench tests (`seed_dsi_bench.py`) should be re-run after each phase
- ConfigHealthGate tests must pass continuously
- Frontend components (PricingTab, RiskTab, etc.) will need updates after Phase A to display new detail fields
- Tower/subscription (Phase E) is the largest lift and may warrant its own design review
