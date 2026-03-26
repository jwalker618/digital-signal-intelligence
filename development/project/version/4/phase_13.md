# Phase 13 — World Engine: Portfolio Intelligence Showcase

## Integrated Portfolio Simulation & Shock Propagation

---

## OVERVIEW

A new top-level section in the DSI app ("World Engine") alongside the existing Pipeline and Referral views. Uses the seeded pipeline data as the portfolio and provides three interactive experiences:

1. **Portfolio Overview** — Aggregate view of the current book: tier distribution, sector concentration, aggregate exposure, risk heatmap
2. **Shock Simulator** — Select a scenario (e.g., "AWS outage", "CISO departure", "regulatory action"), apply it to a sector/coverage/tier segment, see how scores shift across the portfolio
3. **Impact Dashboard** — Before/after comparison: which risks migrated tiers, what's the aggregate premium impact, where are the new concentration hotspots

This demonstrates the Vision Paper's core thesis: *"Because the World Model understands the structure of the portfolio, it can simulate exogenous shocks before they happen."*

---

## DESIGN PRINCIPLES

1. **Portfolio-level, not submission-level** — This is about the book, not individual risks
2. **Pre-computed simulation** — Shock effects are calculated client-side using the existing signal/group/tier data, not via backend round-trips
3. **Visual storytelling** — Charts, heatmaps, and before/after transitions that tell the story at a glance
4. **Connected to the workbench** — Click any affected submission to drill into its workbench view

---

## ARCHITECTURE

### Navigation

- New top-level sidebar item: "World Engine" with a Globe/Orbit icon
- Appears below "Referral Pipeline" in the sidebar navigation
- When selected, renders `WorldEngineView` instead of pipeline tables or workbench

### Data Flow

```
Pipeline Submissions (seeded data)
    │
    ▼
Portfolio Analytics (client-side aggregation)
    │
    ▼
Shock Simulation (client-side recalculation)
    │
    ▼
Impact Dashboard (before/after diff)
```

No new API endpoints needed — everything works from the existing `submissions` array in the store (already fetched by the pipeline) and `activeVersion` data.

---

## IMPLEMENTATION COHORTS

### Cohort A: Portfolio Overview Section

**Purpose**: Aggregate the current book into a portfolio-level dashboard.

| # | Item | Description |
|---|------|-------------|
| A1 | Tier Distribution | Bar chart showing count of submissions per final tier. Clickable bars filter the table below |
| A2 | Sector Concentration | Horizontal bar chart of submissions by coverage type. Shows % concentration per sector |
| A3 | Premium Distribution | Scatter plot: composite score (x) vs premium (y), dots colored by decision |
| A4 | Key Metrics | Total submissions, aggregate premium, average score, average tier, approval rate |
| A5 | Portfolio Table | Sortable table of all submissions with key columns. Click to drill into workbench |

**Effort**: Medium — aggregation logic + Recharts visualisation.

---

### Cohort B: Shock Simulator

**Purpose**: The "What-If Engine" at portfolio scale.

| # | Item | Description |
|---|------|-------------|
| B1 | Scenario Selector | Predefined shock scenarios with name, description, affected dimension, magnitude |
| B2 | Scope Selector | Choose which segment is affected: by coverage, by tier, by score range, or "all" |
| B3 | Shock Application | Client-side: for each affected submission, degrade the composite score by magnitude, recalculate tier using tier_band_interpretation |
| B4 | Animation | Smooth transition as scores shift — dots move on the scatter plot, bars change height |

**Predefined Scenarios:**
- "Critical Vulnerability (CVE)" — Degrades technical signals by 20-30 pts
- "Key Personnel Departure" — Degrades corporate signals by 15-25 pts
- "Regulatory Action" — Degrades compliance signals by 25-35 pts
- "Supply Chain Disruption" — Degrades operational signals by 20-30 pts
- "Market Downturn" — Degrades financial signals by 10-20 pts
- "Data Breach (Industry Peer)" — Degrades behavioral signals by 15-25 pts

**Effort**: Medium — shock logic + UI controls.

---

### Cohort C: Impact Dashboard

**Purpose**: The "Portfolio Steering" consequence view.

| # | Item | Description |
|---|------|-------------|
| C1 | Tier Migration Matrix | Sankey or alluvial diagram: before tiers → after tiers. Shows how many risks migrated |
| C2 | Premium Impact | Total premium before vs after. Delta in $ and %. Breakdown by tier |
| C3 | Decision Changes | How many submissions changed decision (approve→refer, refer→decline) |
| C4 | Concentration Shift | Did the shock create new concentration hotspots? |
| C5 | Most Affected | Table of top 10 most-impacted submissions with score delta, tier change, premium change |

**Effort**: Medium — diff calculation + visualisation.

---

### Cohort D: Navigation & Wiring

| # | Item | Description |
|---|------|-------------|
| D1 | Sidebar item | Add "World Engine" to layout.tsx sidebar (below Referral Pipeline) |
| D2 | View routing | New WorldEngineView.tsx rendered when activeMenu === "World Engine" |
| D3 | Store state | Add `shockScenario` and `shockedPortfolio` to store for shock state management |
| D4 | Drill-through | Click any submission in impact tables to navigate to its workbench |

**Effort**: Small.

---

## EXECUTION ORDER

```
Cohort D (navigation) → Cohort A (portfolio overview) → Cohort B (shock simulator) → Cohort C (impact dashboard)
```

---

## FILES

| File | Action | Cohort |
|------|--------|--------|
| `frontend/src/components/worldengine/WorldEngineView.tsx` | NEW | A, B, C |
| `frontend/src/components/worldengine/PortfolioOverview.tsx` | NEW | A |
| `frontend/src/components/worldengine/ShockSimulator.tsx` | NEW | B |
| `frontend/src/components/worldengine/ImpactDashboard.tsx` | NEW | C |
| `frontend/src/lib/shockEngine.ts` | NEW | B (pure functions) |
| `frontend/src/app/layout.tsx` | EDIT | D1 |
| `frontend/src/app/page.tsx` | EDIT | D2 |
| `frontend/src/store/dsiStore.ts` | EDIT | D3 |

---

## VISUAL CONCEPT

```
┌──────────────────────────────────────────────────────────────────┐
│ WORLD ENGINE                                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─ KEY METRICS ──────────────────────────────────────────────┐  │
│  │ 127 Submissions │ $4.2M Agg Premium │ Avg Score 612 │ ...  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ TIER DISTRIBUTION ─────┐  ┌─ SECTOR CONCENTRATION ────────┐ │
│  │  ██████████████  T1: 42  │  │  Cyber     ████████████  38%  │ │
│  │  ████████████    T2: 35  │  │  D&O       ██████        22%  │ │
│  │  ██████          T3: 28  │  │  PI        ████          15%  │ │
│  │  ████            T4: 15  │  │  Marine    ███           12%  │ │
│  │  ██              T5:  7  │  │  Energy    ██             8%  │ │
│  └──────────────────────────┘  └───────────────────────────────┘ │
│                                                                    │
│  ┌─ SHOCK SIMULATOR ──────────────────────────────────────────┐  │
│  │  Scenario: [Critical Vulnerability ▾]  Scope: [Cyber ▾]    │  │
│  │  Magnitude: ████████░░ 25pts          [APPLY SHOCK]         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ IMPACT ───────────────────────────────────────────────────┐  │
│  │  Tier Migrations: 18 risks moved │ Premium Impact: +$340K   │  │
│  │  Decision Changes: 7 approve→refer │ 3 refer→decline        │  │
│  │                                                              │  │
│  │  MOST AFFECTED:                                              │  │
│  │  TechFlow Solutions   782→641  T2→T3  +$12,400              │  │
│  │  CloudNet Inc         701→589  T2→T3  +$8,200               │  │
│  │  ...                                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## NOTES

- All shock calculations are client-side using the seeded pipeline data — no backend needed
- The tier recalculation reuses `lookupTierFromScore` from `scenarioEngine.ts`
- Recharts provides the charting (already a dependency)
- The scatter plot reuses the decision colour palette from `chartConfig.ts`
- Portfolio data comes from the store's `submissions` array (already fetched by pipeline)
- This is a showcase/prototype — not production portfolio management. The Rust sim engine would power the production version
