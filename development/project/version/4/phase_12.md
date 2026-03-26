# Phase 12 — UX Refinement, Theme System, Code Optimisation

## Comprehensive UX Feedback Response & Infrastructure Hardening

---

## OVERVIEW

This phase addresses all outstanding UX feedback across every tab, introduces a proper theme colour system, fixes the sidebar layout behaviour, adds null safety across the frontend, creates a user context stub, optimises API calls to use projection endpoints, and deduplicates shared code.

---

## COHORT A: Theme System — Replace Hardcoded Colours

**Problem**: 65+ hardcoded hex values and 118+ Tailwind colour utility references (emerald-400, rose-400, amber-400, etc.) that don't adapt between light and dark themes. Chart colours (#94a3b8, #334155, #3b82f6) are baked into Recharts config.

**Solution**: Extend globals.css with semantic colour variables for each role, then replace all hardcoded references.

| # | Item | Description | Files |
|---|------|-------------|-------|
| A1 | Define semantic theme variables | Add to `:root` and `.dark`: `--dsi-positive` (green), `--dsi-negative` (red), `--dsi-warning` (amber), `--dsi-info` (blue), `--dsi-chart-grid`, `--dsi-chart-axis`, `--dsi-chart-tooltip-bg`, `--dsi-chart-tooltip-border`, `--dsi-chart-subject` (the blue crosshair/star), `--dsi-chart-peer` (default dot), plus `/approve`, `/refer`, `/decline` decision colours | `globals.css` |
| A2 | Register in @theme inline | Map `--color-dsi-positive`, etc. for Tailwind utility access | `globals.css` |
| A3 | Replace hex in chart components | Swap all `#10b981`, `#f43f5e`, `#f59e0b`, `#3b82f6`, `#94a3b8`, `#334155`, `#475569`, `#1e293b`, `#0f172a`, `#f8fafc` with CSS variable references. Recharts accepts CSS vars via `var(--dsi-positive)` in style props | `LossTab.tsx`, `ExposureTab.tsx` |
| A4 | Replace Tailwind colour utilities | Swap `text-emerald-400` → `text-dsi-positive`, `text-rose-400` → `text-dsi-negative`, `text-amber-400` → `text-dsi-warning`, `bg-emerald-500/10` → `bg-dsi-positive/10`, etc. across all tabs | All `.tsx` files |
| A5 | Confirm IBM Plex Sans coverage | Verify `font-ibm` is default body font. Only `font-inter` exception is the title bar `<h1>`. Confirm `font-mono` usage is appropriate (code/data display only) | `layout.tsx` — audit only, no changes expected |

**Effort**: Medium. Mostly find-and-replace with careful colour mapping.

---

## COHORT B: Sidebar Layout — Content Slides, Not Shrinks

**Problem**: Sidebar uses `w-[50%]` when expanded, main uses `flex-1` → content compresses from 95% to 50% width. Elements resize and reflow.

**Solution**: Fix the main content area width to remain constant. When the sidebar expands, the main content slides right (partially off-screen) rather than shrinking.

| # | Item | Description | Files |
|---|------|-------------|-------|
| B1 | Fixed main content width | Set main to `w-[95%]` (or `calc(100% - collapsed_sidebar_width)`) instead of `flex-1`. When sidebar expands, main retains its width and overflows off the right edge | `layout.tsx` |
| B2 | Sidebar overlay behaviour | Change sidebar from pushing content to overlaying with a `z-30` layer and optional backdrop dimming | `layout.tsx` |
| B3 | Transition tuning | Ensure smooth `transition-all duration-300` on the translate/margin shift | `layout.tsx` |

**Effort**: Small. CSS-only change to the flex layout strategy.

---

## COHORT C: Null Safety Pass

**Problem**: Many property chains like `activeVersion.base_premium_derivation.basis_value` can be null, causing runtime errors.

**Solution**: Audit every `activeVersion.*`, `activeQuote.*`, `activeSubmission.*` access across all tabs and add optional chaining (`?.`) and fallback defaults (`|| 0`, `|| 'N/A'`, `?? []`).

| # | Item | Description | Files |
|---|------|-------------|-------|
| C1 | activeVersion property access | Add `?.` to all nested JSONB field access: `base_premium_derivation?.basis_value`, `final_premium_detail?.limit`, `exposure_components?.size`, `tier_band_interpretation?.tiers`, `loss_correlation_config?.propensity_bands`, etc. | All tabs + `scenarioEngine.ts` |
| C2 | activeQuote / activeSubmission guards | Ensure `activeQuote?.status`, `activeSubmission?.submission_data?.industry`, etc. never throw | All tabs |
| C3 | Array method guards | All `.map()`, `.filter()`, `.find()` calls on potentially-null arrays need `(arr || []).map(...)` or guard checks | All tabs |
| C4 | Recharts data guards | Charts receiving null/undefined data arrays should get `[]` fallback | `LossTab.tsx`, `ExposureTab.tsx` |

**Effort**: Medium. Tedious but straightforward — every `.tsx` file needs a pass.

---

## COHORT D: SummaryTab Fixes

**Problem**: (1) Notes not shown inline. (2) Active Conditions section shouldn't be on summary.

| # | Item | Description | Files |
|---|------|-------------|-------|
| D1 | Show notes inline | Instead of just "X notes recorded" with a modal-only view, render the last 3 notes directly in the Notes sidebar card. Keep the "Manage →" modal link for full history + adding new notes | `SummaryTab.tsx` |
| D2 | Remove Active Conditions panel | Delete the "Active Flags & Conditions" section from the right column. Conditions belong on the Risk tab, not the executive summary | `SummaryTab.tsx` |

**Effort**: Small.

---

## COHORT E: RiskTab Enhancements

**Problem**: (1) Tier Position needs tier improvement paths. (2) Group scores missing loss/exposure banding context. (3) Signals should nest inside groups as accordions. (4) Group-level conditions missing. (5) Direct queries not shown.

| # | Item | Description | Files |
|---|------|-------------|-------|
| E1 | Tier improvement paths | Below the tier gauge, add "Paths to Tier {N-1}" section: using `tier_band_interpretation`, show the target score range, the points needed to get there, and which groups contribute the most to the current score (sorted by contribution descending) — these are the levers an underwriter could pull | `RiskTab.tsx` |
| E2 | Group scores: loss/exposure banding | Add columns to the Group Score Summary table: `Loss Band` (lookup group's loss score against `loss_band_interpretation`), `Exposure Band` (lookup against `exposure_band_interpretation`). Shows how each group's contribution maps to eventual banding | `RiskTab.tsx` |
| E3 | Signal accordion inside groups | Replace the flat signal table with an expandable group accordion (matching PricingTab pattern). Each group row shows: group_code, risk_score, risk_weight, contribution, coverage ratio, loss/exposure weights + bands. Clicking expands to show underlying signals with their scores/weights/contributions | `RiskTab.tsx` |
| E4 | Group-level conditions | In each group's accordion header, show condition badges for any conditions where `source_type === 'signal_group'` AND `source_id` matches the group code. Currently only signal-level conditions are shown | `RiskTab.tsx` |
| E5 | Direct query display | Add a "Direct Queries" section showing `query_conditions` with their source, response, action, and note. Currently we show them mixed into "Active Conditions" but the queries themselves (question + response) are not visible | `RiskTab.tsx` |

**Effort**: Large. Major restructure of the signal table into an accordion.

---

## COHORT F: ScenarioTab Improvements

**Problem**: (1) Signals should use group accordion (not flat table). (2) Need group-level override (proportional distribution). (3) Loss/exposure override too binary. (4) Cascade must match PricingTab style.

| # | Item | Description | Files |
|---|------|-------------|-------|
| F1 | Group accordion with signals | Replace flat signal table with expandable groups (same pattern as E3). Group header shows group score + scenario group score. Expand to see individual signals with stepper inputs | `ScenarioTab.tsx` |
| F2 | Group-level override input | In each group's accordion header, add a group-level score override input. When changed, the delta is distributed proportionally by weight across all signals in that group. E.g., if group has signals weighted 0.5, 0.3, 0.2 and user increases group by +10, signals get +5, +3, +2 respectively | `ScenarioTab.tsx`, `scenarioEngine.ts` |
| F3 | Loss modifier detail | Replace simple number input with a card showing: current propensity score → band → freq/sev multipliers → combined. When signal overrides change, show the recalculated values from `loss_correlation_config`. Still allow direct override but show the calculated path first | `ScenarioTab.tsx` |
| F4 | Exposure modifier detail | Similar to F3: show current exposure value → band → modifier from `exposure_band_interpretation`. Allow override but show the lookup path | `ScenarioTab.tsx` |
| F5 | Cascade matches PricingTab | Restyle the cascade waterfall to use the PricingTab's 4-column grid pattern (`grid-cols-[50%_10%_20%_20%]`) with the same chevron expand/collapse for modifier groups, same visual treatment for ILF/deductible/guardrails. Add an "Original" column and "Scenario" column | `ScenarioTab.tsx` |

**Effort**: Large. Full restructure of the ScenarioTab UI.

---

## COHORT G: ReferralTab Fixes

**Problem**: (1) Signal Audit Matrix shows no data (wrong fetch). (2) Needs group accordion alignment. (3) Needs correct endpoint wiring for overrides.

| # | Item | Description | Files |
|---|------|-------------|-------|
| G1 | Fix signal data fetch | Replace `fetchReferralSignals(activeSubmission.model_version_id)` with `fetchRiskSignals(activeVersion.version_code)`. The `model_version_id` field isn't in the API type | `ReferralTab.tsx` |
| G2 | Group accordion for audit | Restructure the Signal Audit Matrix to use the same group → signal accordion pattern from E3/F1. Group headers show group totals, expand to individual signals with audit columns (inferred value, audited value, rationale, impact, action button) | `ReferralTab.tsx` |
| G3 | Override endpoint verification | Verify that `submitSignalOverride(quoteCode, signalCode, auditedValue, rationale)` correctly calls `POST /api/v1/signals/{quoteCode}/override` and that this creates a new model version. Add error handling and success feedback | `ReferralTab.tsx`, `dsiStore.ts` |

**Effort**: Medium.

---

## COHORT H: User Context Stub

**Problem**: No user identity. Actions (ROL selection, note creation, signal overrides) are recorded as "system" with no audit trail of who performed them.

| # | Item | Description | Files |
|---|------|-------------|-------|
| H1 | Create UserContext | Create `frontend/src/context/UserContext.tsx` with a React context providing `{user_id, display_name, role}`. Default to `{user_id: 'anon', display_name: 'Anonymous', role: 'underwriter'}` | NEW: `context/UserContext.tsx` |
| H2 | Wrap app in provider | Add `<UserProvider>` to `layout.tsx` around the app content | `layout.tsx` |
| H3 | Wire into store actions | Update `submitSignalOverride`, `selectLimitOption`, `updateDecision` to include `user_id` from context. Update `handleAddNote` in SummaryTab to use context display_name instead of hardcoded "Underwriter_UI" | `dsiStore.ts`, `SummaryTab.tsx`, `ReferralTab.tsx` |

**Effort**: Small.

---

## COHORT I: API Projection Optimisation

**Problem**: `fetchCoreSubmissionDetail` calls `/modelversion/{code}/all` returning the full ~100-field record. Each tab only uses a subset.

**Solution**: Use projection endpoints for tab-specific data. Keep `/all` for the initial hydration but use projections for targeted refreshes.

| # | Item | Description | Files |
|---|------|-------------|-------|
| I1 | Add projection fetch functions | Add to store: `fetchVersionBase(code)`, `fetchVersionLoss(code)`, `fetchVersionExposure(code)`, `fetchVersionDetail(code)`, `fetchVersionCommentary(code)`. Each calls the corresponding `/base`, `/loss`, `/exposure`, `/detail`, `/commentary` endpoint | `dsiStore.ts` |
| I2 | Tab-specific hydration | When switching tabs, fetch only the projection needed: RiskTab → `/detail`, LossTab → `/loss`, ExposureTab → `/exposure`, PricingTab → `/base`, SummaryTab → `/commentary`. Merge into `activeVersion` state | `dsiStore.ts` |
| I3 | Lazy loading pattern | Only fetch projection data when the user navigates to that tab for the first time. Cache in store to avoid re-fetching on tab switches | `dsiStore.ts` |

**Effort**: Medium. Store architecture change.

---

## COHORT J: Code Deduplication

**Problem**: Organic growth has created significant repetition — identical sticky headers, condition rendering, chart tooltip configs, section card wrappers duplicated across 8+ tabs.

| # | Item | Description | Files |
|---|------|-------------|-------|
| J1 | Extract StickyHeader component | The sticky Key Details header (status + quote dates + submission/quote codes) is copy-pasted in every tab. Extract to `components/shared/StickyHeader.tsx` | NEW + all tabs |
| J2 | Extract SectionCard component | The rounded card with header bar + body pattern (flex flex-col, rounded-t-xl header, rounded-b-xl body with border-b-3) is repeated ~40 times. Extract to `components/shared/SectionCard.tsx` with `title`, `icon`, `headerRight` props | NEW + all tabs |
| J3 | Extract ConditionsList component | The condition rendering block (action colours, badge, note, source_type) is duplicated in RiskTab, LossTab, ExposureTab, SummaryTab, ReferralTab. Extract to `components/shared/ConditionsList.tsx` | NEW + 5 tabs |
| J4 | Extract chart tooltip config | The `tooltipStyle` object and `DECISION_COLORS` map are duplicated in LossTab and ExposureTab. Move to a shared constants file | NEW: `lib/chartConfig.ts` |
| J5 | Extract formatNum / fmtDollar | Helper functions duplicated across tabs. Move to `lib/format.ts` | NEW + all tabs |

**Effort**: Medium. Careful refactoring — must not change visual output.

---

## EXECUTION ORDER

```
Cohort A (theme)  ─────────────────────────────────────────────┐
Cohort B (sidebar)  ───────────────────────────────────────────┤
Cohort C (null safety)  ───────────────────────────────────────┤── Infrastructure
Cohort H (user context)  ──────────────────────────────────────┘
                                                                │
Cohort J (deduplication)  ─────────────────────────────────────── Shared components
                                                                │
Cohort D (SummaryTab)  ────────────────────────────────────────┐
Cohort E (RiskTab)  ───────────────────────────────────────────┤── Tab-specific
Cohort F (ScenarioTab)  ───────────────────────────────────────┤
Cohort G (ReferralTab)  ───────────────────────────────────────┘
                                                                │
Cohort I (API projections)  ─────────────────────────────────── Performance
```

**Critical path**: J must happen before D/E/F/G so that the extracted shared components are available when restructuring tabs.

**Parallel opportunities**: A, B, C, H can all execute independently. D/E/F/G can execute in parallel once J is complete.

---

## NOTES

- Visual output must not change (per user instruction) — only internal structure improves
- The sidebar fix (B) uses an overlay approach so expanded sidebar doesn't disturb content layout
- The group accordion pattern (E3/F1/G2) should be a shared component since it's used in 3 tabs
- Migration 007 for config snapshots was already created in Phase 11 — main also has a 007 for commercial/risk terms. These will need reconciliation (renumber ours to 008)
- IBM Plex Sans is confirmed as the global font; Inter is intentionally title-bar only
