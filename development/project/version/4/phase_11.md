# Phase 11 — Scenario Engine & Full-Visibility Recalculation

## ScenarioTab: Client-Side Pricing Cascade from Signal Overrides

---

## OVERVIEW

The ScenarioTab replaces the scenario sandbox previously embedded in the RiskTab. It provides a **complete client-side recalculation engine** that cascades signal score overrides through every pricing stage — composite score, tier assignment, base premium, loss/exposure modifiers, ILF, deductible factor, guardrail capping — producing an instant "what-if" premium without backend round-trips.

**Prerequisite**: Five config snapshot JSONB columns added to `model_versions` (migration 007) — `loss_correlation_config`, `ilf_curve_config`, `deductible_factor_table`, `exposure_modifier_config`, `guardrails_config`. These are already implemented.

**File**: `frontend/src/components/submissions/Workbench/ScenarioTab.tsx`

---

## DESIGN PRINCIPLES

1. **Original vs Scenario**: Every calculated value is shown as a side-by-side comparison (original → scenario) with delta highlighting
2. **Top-down cascade**: The UI reads top-to-bottom as the calculation flows — signals at top, final premium at bottom
3. **Override isolation**: Each override (signal score, loss modifier, exposure modifier, limit, deductible) is independently adjustable — the cascade recomputes from the first changed value downward
4. **Config-driven**: All recalculation uses persisted config snapshots from `activeVersion`, never hardcoded values
5. **Graceful degradation**: If a config snapshot is missing (older records), that cascade stage shows "held constant" and uses the original value

---

## IMPLEMENTATION COHORTS

### Cohort A: Recalculation Engine (Pure Functions)

**Purpose**: Standalone pure functions with zero UI concerns. These can be unit-tested independently.

**File**: `frontend/src/lib/scenarioEngine.ts` (NEW)

| # | Function | Input | Output | Notes |
|---|----------|-------|--------|-------|
| A1 | `recalcCompositeScore` | signal scores + group weights | composite score (0-1000) | Port from existing RiskTab `useMemo` logic |
| A2 | `lookupTierFromScore` | composite score + `tier_band_interpretation` | `{tier, label, action, application}` | Linear scan through band ranges |
| A3 | `recalcBasePremium` | tier application + `base_premium_derivation` | base premium ($) | PREMIUM_BASE: direct value; MULTIPLIER: basis × rate |
| A4 | `recalcLossModifier` | signal overrides + group_scores + `loss_correlation_config` | `{propensity_score, band, freq_mult, sev_mult, combined}` | Weighted average → invert → band lookup → combine |
| A5 | `recalcExposureModifier` | exposure_value + `exposure_band_interpretation` | `{band_label, modifier}` | Band range lookup (already available from existing snapshot) |
| A6 | `applyModifierChain` | base premium + `modifiers_applied[]` + override loss/exposure | `{premium_after_mods, total_modifier, waterfall[]}` | Replay modifier chain, substituting overridden values |
| A7 | `recalcILF` | limit + `ilf_curve_config` | ILF factor | Parametric curve evaluation (power/iso_pareto/bounded_exp/log) |
| A8 | `recalcDeductibleFactor` | deductible + product_type + `deductible_factor_table` | factor | Simple table lookup |
| A9 | `applyGuardrails` | total_modifier + final_premium + limit + revenue + `guardrails_config` | `{clamped_modifier, capped_premium, warnings[]}` | Floor/cap/ratio checks |
| A10 | `runFullCascade` | all overrides + all configs | `ScenarioResult` with every intermediate value | Orchestrator calling A1→A9 in sequence |

**Effort**: Medium — ~200 lines of pure TypeScript, mostly arithmetic and lookups.

---

### Cohort B: ScenarioTab Skeleton & State Management

**Purpose**: The React component shell — imports, store wiring, override state declarations, reset logic. No cascade output yet — just the container.

**File**: `frontend/src/components/submissions/Workbench/ScenarioTab.tsx` (NEW)

| # | Item | Description |
|---|------|-------------|
| B1 | Store wiring | `activeVersion`, `activeSubmission`, `activeQuote`, `riskSignals`, `fetchRiskSignals` |
| B2 | Override state | `signalOverrides: Record<string, number>`, `lossModifierOverride: number|null`, `exposureModifierOverride: number|null`, `limitOverride: number|null`, `deductibleOverride: number|null` |
| B3 | Reset action | Single button clears all overrides back to null |
| B4 | Cascade memo | `useMemo` calling `runFullCascade()` from Cohort A, recomputing whenever any override changes |
| B5 | Sticky header | Standard Key Details header (matching other tabs) |
| B6 | Empty content area | Placeholder sections for Cohorts C/D/E to fill |

**Effort**: Small — ~80 lines, mostly boilerplate.

---

### Cohort C: Signal Override Table

**Purpose**: The interactive signal table where underwriters adjust individual scores. Moved from the old RiskTab with the scenario columns retained.

| # | Item | Description |
|---|------|-------------|
| C1 | Signal table | Group → Signal Code → Score → Weight → Contribution columns (read-only originals) |
| C2 | Scenario column | Stepper + input field for each signal (port from old RiskTab) |
| C3 | New contribution column | Recalculated contribution per signal based on override |
| C4 | Group subtotals | Show per-group score subtotal (original vs scenario) |
| C5 | Composite score header | Original composite vs scenario composite with delta, shown above the table |

**Effort**: Medium — ~150 lines. Largely ported from old RiskTab signal table.

---

### Cohort D: Cascade Waterfall Display

**Purpose**: The visual representation of the full pricing cascade — a vertical waterfall showing each stage from composite score down to final premium, with original vs scenario side-by-side.

| # | Item | Description |
|---|------|-------------|
| D1 | Tier resolution row | Score → Tier lookup. Shows: original tier vs scenario tier, band ranges, action (approve/refer/decline) |
| D2 | Base premium row | Tier → Base premium. Shows: method (PREMIUM_BASE/MULTIPLIER), basis, rate, result |
| D3 | Modifier waterfall | Each modifier in sequence: source name, original factor, scenario factor (highlighted if loss/exposure changed), running premium |
| D4 | ILF row | Limit → ILF factor → scaled premium. Shows curve type, anchor, factor at current vs scenario limit |
| D5 | Deductible row | Deductible → factor → adjusted premium |
| D6 | Guardrail row | Cap checks: modifier clamp, premium-to-limit ratio, premium-to-revenue ratio. Red highlight if any cap binds |
| D7 | Final premium row | Bold final result with total delta from original |

**Layout**: Each row is a card with `Original | → | Scenario` three-column layout. Changed values highlighted in `text-dsi-selected`. The waterfall reads top-to-bottom matching the actual calculation flow.

**Effort**: Medium — ~200 lines of structured display.

---

### Cohort E: Direct Override Controls

**Purpose**: Slider/input controls for directly overriding loss modifier, exposure modifier, limit, and deductible — bypassing the signal-level recalculation for quick what-if exploration.

| # | Item | Description |
|---|------|-------------|
| E1 | Loss modifier override | Number input with ±0.01 steppers. When set, overrides the loss_combined_modifier in the cascade (bypasses A4). Shows "calculated: X.XXx → override: Y.YYx" |
| E2 | Exposure modifier override | Same pattern as E1 for exposure_modifier |
| E3 | Limit selector | Dropdown/input for limit amount. Drives ILF recalculation via A7. Shows available limits from `limit_premiums` if present |
| E4 | Deductible selector | Dropdown from `deductible_factor_table` entries. Drives A8 |
| E5 | Override indicators | Visual badges on each control showing "overridden" vs "calculated" state |

**Layout**: Horizontal row of compact controls between the signal table (Cohort C) and the waterfall (Cohort D). Acts as the bridge between "signal-level what-if" and "pricing-level what-if".

**Effort**: Small — ~100 lines.

---

### Cohort F: Navigation Registration

**Purpose**: Wire the new tab into the workbench.

| # | Item | Description |
|---|------|-------------|
| F1 | WorkbenchView.tsx | Add import + case for `"Scenarios"` → `<ScenarioTab/>` |
| F2 | layout.tsx | Add `{ name: "Scenarios", icon: FlaskConical }` to sidebar menu items (after Risk Assessment) |

**Effort**: Trivial — 4 lines across 2 files.

---

## EXECUTION ORDER

```
Cohort A (engine)     ──→  Cohort B (skeleton)  ──→  Cohort C (signals)
                                    │
                                    ├──→  Cohort E (override controls)
                                    │
                                    └──→  Cohort D (waterfall)
                                                    │
                                              Cohort F (navigation)
```

A must be complete before B (B calls A). B must exist before C/D/E (they render inside B's shell). F is last.

---

## RECALCULATION CHAIN DETAIL

```
Signal Overrides (user)
    │
    ▼
┌─ A1: Composite Score ──────────────────────────────────┐
│  For each group:                                        │
│    group_score = Σ(signal_score × weight) / Σ(weights)  │
│  composite = Σ(group_score × group_weight × 10)         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A2: Tier Lookup ──────────────────────────────────────┐
│  Scan tier_band_interpretation.tiers[]                   │
│  Find band where bands.min ≤ composite ≤ bands.max      │
│  Return: tier_id, label, action, application             │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A3: Base Premium ─────────────────────────────────────┐
│  If PREMIUM_BASE: base = application.value               │
│  If MULTIPLIER: base = basis_value × application.applied │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A4: Loss Modifier (if signal overrides present) ──────┐
│  For each loss group (groups with loss_weight > 0):      │
│    avg_score = Σ(signal_score × loss_weight) / Σ(lw)    │
│  propensity = 100 - avg_score (invert)                   │
│  Lookup propensity_bands → frequency_multiplier          │
│  Lookup severity_bands → severity_multiplier             │
│  combined = freq_mult × freq_weight + sev_mult × sev_wt │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A6: Modifier Chain ───────────────────────────────────┐
│  premium = base_premium                                  │
│  For each modifier in modifiers_applied[]:               │
│    If source is "loss" → use scenario loss modifier      │
│    If source is "exposure" → use scenario exposure mod   │
│    Else → use original factor                            │
│    premium = premium × factor                            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A7: ILF ──────────────────────────────────────────────┐
│  Evaluate parametric curve at scenario limit:            │
│    power: (L/anchor)^alpha                               │
│    iso_pareto: 1-(b/(b+L))^(q-1)                        │
│    bounded_exp: 1+(max-1)×(1-exp(-k×L/anchor))          │
│  Normalize: ILF(L) / ILF(anchor) = factor               │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A8: Deductible Factor ───────────────────────────────┐
│  Lookup deductible_factor_table[product_type]            │
│  Find matching deductible → factor                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─ A9: Guardrails ──────────────────────────────────────┐
│  Clamp total_modifier to [floor, cap]                    │
│  final = premium_after_mods × ILF × ded_factor          │
│  Cap vs limit × max_premium_to_limit_ratio               │
│  Cap vs revenue × max_premium_to_revenue_ratio           │
└─────────────────────────────────────────────────────────┘
    │
    ▼
  Final Scenario Premium ($)
```

---

## FILES AFFECTED

| File | Action | Cohort |
|------|--------|--------|
| `frontend/src/lib/scenarioEngine.ts` | NEW | A |
| `frontend/src/components/submissions/Workbench/ScenarioTab.tsx` | NEW | B, C, D, E |
| `frontend/src/components/submissions/WorkbenchView.tsx` | EDIT (add import + case) | F |
| `frontend/src/app/layout.tsx` | EDIT (add sidebar menu item) | F |

---

## NOTES

- The RiskTab has already been rewritten as a read-only assessment viewer (this session). The scenario sandbox was removed from it.
- Config snapshot columns and seeder builders are already implemented (migration 007, this session).
- The `scenarioEngine.ts` functions are intentionally separated from the component so they can be reused by other tabs or tested independently.
- If `ilf_curve_config` is null (older records), the ILF stage holds constant at the stored `ilf_factor` value. Same graceful degradation for all config snapshots.
- Loss modifier recalculation (A4) requires both `loss_correlation_config` AND the individual signal scores mapped to loss groups via `group_scores[group].loss_weight`. If the correlation config isn't available, the loss modifier is held constant and the user can still override it directly via E1.
