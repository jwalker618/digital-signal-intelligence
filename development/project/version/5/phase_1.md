# Version 5 Phase 1: UX Conversion for Commercial & Risk Terms

## Overview

Convert the DSI frontend workbench from a flat tab structure (8 technical assessment tabs) to a categorized structure with four top-level sections: **Summary**, **Commercial**, **Risk**, and **Technical**. This integrates the commercial_terms and risk_terms entities that were added in Version 4 into the underwriter workflow.

## Current State

The workbench (`frontend/src/components/submissions/WorkbenchView.tsx`) presents 8 flat tabs in the sidebar when a submission is selected:

1. Summary
2. Pricing Anatomy
3. Risk Assessment
4. Loss Assessment
5. Exposure Assessment
6. Scenarios
7. Referral Actions
8. Model Versions

The backend already has full support for commercial terms and risk terms:
- DB tables: `commercial_terms`, `risk_terms` (migration 007)
- ORM models: `CommercialTermsRecord`, `RiskTermsRecord`
- Schema: `infrastructure/models/commercial_schema.py`
- API routes: `infrastructure/api/routes/commercial.py`
- Entity YAML: `commercial/entities/*.yaml`
- Premium assembly: `layers/risk/premium_assembly.py`
- FX conversion: `layers/risk/fx.py`
- Seed data: Already generates both record types for all companies

## Target State

### Navigation Structure

```
Submission Selected
  |
  +-- Summary (cross-cutting overview)
  |     Shows decision, key metrics from all three categories
  |
  +-- Commercial
  |     +-- Terms Overview (entity economics, FX, commission)
  |     +-- Premium Assembly (technical -> net -> gross -> offered)
  |     +-- Distribution (subscription/tower/direct structure)
  |
  +-- Risk
  |     +-- Deductible Structure (type, amount, basis)
  |     +-- Coverage Terms (extensions, exclusions, sub-limits)
  |     +-- SIR & Waiting Periods
  |     +-- Aggregate & Reinstatement
  |
  +-- Technical
  |     +-- Pricing Anatomy (existing PricingTab)
  |     +-- Risk Assessment (existing RiskTab)
  |     +-- Loss Assessment (existing LossTab)
  |     +-- Exposure Assessment (existing ExposureTab)
  |     +-- Scenarios (existing ScenarioTab)
  |     +-- Referral Actions (existing ReferralTab)
  |     +-- Model Versions (existing ModelVersionsTab)
```

### Summary Tab Evolution

The Summary tab becomes a cross-cutting overview showing key data from all three categories:

**Current Summary content** (retain):
- Decision banner (approve/refer/decline)
- WHO/Discovery cards
- Base details (coverage, limit, premium)
- Three-pillar assessment cards (risk, exposure, loss)

**New Summary content** (add):
- Commercial headline: Entity name, offered premium, gross premium, currency
- Risk terms headline: Deductible type/amount, SIR if applicable, key exclusions count
- Quick navigation links to each category

### Sidebar Changes

The sidebar navigation changes from a flat list to a grouped structure:

```tsx
// Current: flat list
const TABS = [
  { name: "Summary", icon: FolderKanban },
  { name: "Pricing Anatomy", icon: Calculator },
  // ...8 items
];

// New: grouped with category headers
const TAB_GROUPS = [
  { category: "Summary", icon: LayoutDashboard, tabs: [] },
  {
    category: "Commercial",
    icon: Building2,
    tabs: [
      { name: "Terms Overview", icon: FileText },
      { name: "Premium Assembly", icon: Calculator },
      { name: "Distribution", icon: Network },
    ],
  },
  {
    category: "Risk",
    icon: Shield,
    tabs: [
      { name: "Deductible Structure", icon: Layers },
      { name: "Coverage Terms", icon: FileCheck },
      { name: "SIR & Waiting Periods", icon: Clock },
      { name: "Aggregate & Reinstatement", icon: RefreshCw },
    ],
  },
  {
    category: "Technical",
    icon: ChartNoAxesGantt,
    tabs: [
      { name: "Pricing Anatomy", icon: Calculator },
      { name: "Risk Assessment", icon: ChartNoAxesGantt },
      // ...existing tabs
    ],
  },
];
```

## Implementation Plan

### Phase 1a: Sidebar Restructuring (Frontend Only)

**Scope**: Convert flat tab navigation to grouped categories.

**Files to modify**:
- `frontend/src/app/layout.tsx` - Sidebar navigation structure
- `frontend/src/stores/dsiStore.ts` - Add category state management

**Changes**:
1. Replace flat `TABS` array with `TAB_GROUPS` structure
2. Add category headers with expand/collapse behavior
3. "Summary" remains a top-level item (not nested)
4. Default expanded category: last used or first with data
5. Active tab highlighting within category context

**No backend changes required.**

### Phase 1b: Commercial Terms Tab

**Scope**: Create CommercialTermsTab component.

**New files**:
- `frontend/src/components/submissions/Workbench/CommercialTermsTab.tsx`

**Data source**: `GET /commercial/{model_version_code}` API endpoint (already exists)

**Content sections**:
1. **Entity Identity**: Entity name, market, base currency
2. **Premium Waterfall**: Technical premium -> deductions (brokerage, overrider) -> net premium -> taxes/levies -> gross premium -> offered premium
3. **Commission Structure**: Brokerage rate, overrider, profit commission (with loss ratio threshold if applicable)
4. **FX Context**: Base currency, settlement currency, FX rate, rate source, rate date
5. **Distribution Structure**: Type (direct/subscription/tower/bundled), signed line, role, lead loading
6. **Offered Premium**: Amount, discretion applied, set by user, minimum premium
7. **Written/Earned Period**: Inception, expiry, earned dates

**Patterns**: Follow existing tab patterns (SectionCard, sticky KPI header, grid layouts).

### Phase 1c: Premium Assembly Tab

**Scope**: Visual breakdown of premium assembly pipeline.

**New files**:
- `frontend/src/components/submissions/Workbench/PremiumAssemblyTab.tsx`

**Content**:
1. **Assembly Waterfall Chart**: Visual flow from technical premium to offered premium
2. **Deduction Breakdown**: Per-component deductions (brokerage, overrider, fronting fee, profit commission)
3. **Tax & Levy Breakdown**: IPT, stamp duty, regulatory levy, fire service levy
4. **Minimum Premium Check**: Whether minimum premium applies, what the floor is
5. **Discretion Analysis**: How offered premium relates to technical, what discretion was applied

### Phase 1d: Distribution Tab

**Scope**: Show subscription/tower/direct distribution details.

**New files**:
- `frontend/src/components/submissions/Workbench/DistributionTab.tsx`

**Content**:
- For DIRECT: Simple display of "100% written" with entity details
- For SUBSCRIPTION: Signed line %, role (lead/follow), lead loading factor, order premium vs line premium
- For TOWER: Layer diagram showing attachment points, per-layer premiums, participation
- For BUNDLED: Package structure showing package limits and premiums

### Phase 1e: Risk Terms Tabs

**Scope**: Create four risk terms sub-tabs.

**New files**:
- `frontend/src/components/submissions/Workbench/DeductibleStructureTab.tsx`
- `frontend/src/components/submissions/Workbench/CoverageTermsTab.tsx`
- `frontend/src/components/submissions/Workbench/SIRWaitingPeriodsTab.tsx`
- `frontend/src/components/submissions/Workbench/AggregateReinstatementTab.tsx`

**Data source**: Risk terms loaded via commercial terms API (risk_terms is FK to commercial_terms).

**Content per tab**:
- **Deductible Structure**: Type (per_occurrence, aggregate, each_and_every), amount, currency, basis
- **Coverage Terms**: Extensions (JSONB), exclusions (JSONB), coverage territory, coverage trigger
- **SIR & Waiting Periods**: SIR amount/currency, waiting period hours/basis (cyber BI), applicable coverage parts
- **Aggregate & Reinstatement**: Aggregate limit, aggregate deductible, reinstatement provisions, co-insurance details

### Phase 1f: Summary Tab Enhancement

**Scope**: Add commercial and risk term headlines to existing Summary tab.

**Files to modify**:
- `frontend/src/components/submissions/Workbench/SummaryTab.tsx`

**New sections** (added below existing three-pillar cards):
1. **Commercial Summary Card**: Entity, offered premium, gross premium, currency, distribution type
2. **Risk Terms Summary Card**: Deductible type/amount, SIR status, key terms count, coverage territory

### Phase 1g: Store & API Integration

**Files to modify**:
- `frontend/src/stores/dsiStore.ts` - Add commercialTerms and riskTerms state
- API fetch methods for commercial terms data

**New store properties**:
```typescript
commercialTerms: CommercialTerms | null;
riskTerms: RiskTerms | null;
isFetchingTerms: boolean;
fetchCommercialTerms: (versionCode: string) => Promise<void>;
```

## Constraints & Principles

1. **No backend changes for Phase 1**: All API endpoints and data already exist
2. **Existing tabs unchanged**: Technical tabs work exactly as before, just nested under "Technical" category
3. **Progressive disclosure**: Commercial and Risk categories can be empty/disabled if no terms exist for a submission
4. **Follow existing patterns**: Use same SectionCard, sticky headers, grid layouts, color schemes
5. **Mobile-aware**: Category headers must work with collapsed sidebar

## Risks & Mitigations

| Risk | Mitigation |
|-|-|
| Sidebar becomes too deep with 4 levels | Categories are collapsible; only one expanded at a time |
| Commercial terms may not exist for all submissions | Show "No commercial terms" state gracefully |
| Navigation state gets complex | Simple Zustand store with activeCategory + activeTab |
| Existing tests may break | Phase 1a is sidebar-only; existing tab components unchanged |

## Dependencies

- Version 4 complete (all coverage expansions done, calibration passing)
- Commercial terms API endpoints functional
- Seed script generating both commercial_terms and risk_terms records

## Success Criteria

1. All 4 categories visible in sidebar with correct grouping
2. Summary tab shows cross-cutting data from all categories
3. Commercial tabs render real data from commercial_terms API
4. Risk tabs render real data from risk_terms API
5. All existing Technical tabs work identically to current behavior
6. Calibration harness still passes for all coverages
7. Seed script generates data visible in all new tabs
