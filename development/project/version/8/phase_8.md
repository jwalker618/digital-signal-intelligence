# Version 8 Phase 8: Frontend Integration

## Overview

Single cohesive pass over the `frontend/` codebase to add the **Client Portal**: a separate Next.js route group with role-aware shells for `BROKER` and `CLIENT` users, five portal pages, and small carrier-side affordances to raise queries on referrals.

This is the **only** phase that touches frontend code (with the single-line exception of `frontend/src/types/auth.ts` in Phase 1). All backend phases (1–7) must be complete and green before Phase 8 starts.

## Rationale

Backend-first means the API surface, data model, and demo state are all stable before any UI is built. The frontend in Phase 8 is purely an integration pass — calling `/api/v1/portal/*` endpoints, rendering responses, threading user actions back to existing endpoints. No backend gaps should be discovered here; if they are, they are tracked as v8.1.

Per the planning decision ("Both, equally"), broker and client get parity — both audiences have their own overview page, both see score/peers/actions/submissions tailored to their context.

Per the planning decision ("Live click-through"), Phase 8's acceptance gate is **the seven-act demo runs end-to-end in a browser**, not just unit tests.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Route structure | New route group `src/app/(portal)/` parallel to existing carrier routes | Separate layouts, shared components |
| Login routing | Existing `/login` page; post-login redirect based on role | Single login surface; no separate broker portal URL |
| Portal layout | Distinct shell with portal-specific nav | Brokers and clients see the same shell with different nav items |
| Branding | Neutral DSI branding (broker logo could be displayed but layout is neutral) | Confirm via the parent v8 plan; portal carries DSI brand chrome with the broker as text label |
| Component reuse | Reuse `frontend/src/components/base/` primitives, charts, cards | Don't reinvent; extend |
| State management | Existing Zustand pattern from `frontend/src/store/` | No new state library |
| Data fetching | Reuse whatever pattern the carrier app uses (likely fetch + SWR or React Query) | Match existing pattern |
| Forms | Reuse existing form primitives | No new form library |
| Charts | Reuse `frontend/src/components/base/charts/primatives.tsx` | Single chart toolkit |
| Carrier-side additions | Add a "Raise query" affordance on the referral detail view (existing UI) | Small modal/inline form; calls Phase 5 endpoint |

## Current State

- Next.js 14 App Router. Single carrier-facing app under `src/app/`.
- Auth guard wraps all routes (`SessionGuard.tsx` from `frontend/src/components/auth/`).
- Permissions UI handled via `PermissionGate` (`frontend/src/components/shared/PermissionGate.tsx`).
- Existing nav config at `frontend/src/components/layout/navConfig.ts`.
- Design tokens at `frontend/src/styles/theme.css`.
- Base components at `frontend/src/components/base/` (cards, modal, charts).
- Theme store at `frontend/src/store/themeStore.ts`.
- Phase 1 added `BROKER` and `CLIENT` to `frontend/src/types/auth.ts` Role enum.

## Target State

### Directory layout

```
frontend/src/app/
  (carrier)/                  # existing — move existing routes under this group
    layout.tsx                # existing carrier shell (re-homed)
    page.tsx                  # existing dashboard
    admin/...
    profile/...
    world-engine/...
  (portal)/                   # NEW
    layout.tsx                # portal shell with portal nav
    overview/page.tsx
    score/page.tsx
    peers/page.tsx
    actions/page.tsx
    submissions/page.tsx
    submissions/[id]/page.tsx
    queries/page.tsx          # broker-only; redirect for client role
  login/                      # existing — moves OUT of either group, top-level (no auth)
    page.tsx
    reset-password/page.tsx
  layout.tsx                  # root layout — no auth gating; route groups handle their own
```

**Route group rename**: existing carrier routes move under `(carrier)/`. This is a directory move only — file contents unchanged. App Router groups don't affect URLs.

### Role-aware redirect on login

After successful login in `frontend/src/app/login/page.tsx`:

```ts
switch (user.role) {
  case Role.BROKER:
  case Role.CLIENT:
    router.push("/overview");          // portal landing
    break;
  default:
    router.push("/");                  // carrier landing
}
```

### Portal layout (`src/app/(portal)/layout.tsx`)

- Wraps in `SessionGuard`.
- Renders portal-specific nav. Nav items:
  - **Broker** sees: Overview, Queries, Submissions
  - **Client** sees: Overview, Score, Peers, Actions, Submissions
  - Profile is shared.
- Top bar with user identity, role chip, broker name (if BROKER).
- Theme toggle from existing `themeStore`.

A new `frontend/src/components/portal/PortalNav.tsx` renders nav items based on role. Single component, role conditional inside.

### Page: `/overview`

**Broker view:**
- Top: "Book of Clients" heading, count.
- Table: client name, coverage, score, tier (badge), percentile rank, premium, renewal date, open queries flag.
- Row click → `/submissions/{submission_id}` for that client.
- Backed by `GET /api/v1/portal/overview`.

**Client view:**
- Top: entity name, broker badge.
- Card: current cyber quote with score, tier, percentile, premium.
- Quick links to Score, Peers, Actions.
- Backed by same `GET /api/v1/portal/overview` (response shape differs by role).

### Page: `/score`

Client view (broker can also view, scoped to a specific client via deep link).

- Headline numbers: score, tier, premium, premium without strengths/with drags.
- **Strengths panel**: list of positive drivers from `impact_breakdown.strengths`, each with signal label, dollar reduction, percentage.
- **Drags panel**: same shape for `impact_breakdown.drags`, sorted by absolute impact. Each row clickable → opens remediation drawer (from Phase 4 data).
- **Neutral signals** collapsed into a "X signals with negligible impact" footer.
- Visual: simple horizontal bar chart of premium build-up (base → strengths reduce → drags increase → final).

Backed by `GET /api/v1/portal/entities/{id}/score`.

For broker accessing a client's score: deep link `/score?entity_id=101`. Page extracts entity_id from query string; otherwise defaults to the user's own entity (for CLIENT role).

### Page: `/peers`

- Headline: "You rank in the Xth percentile of N peers."
- Bell-curve viz of cohort score distribution, with the entity's position marked.
- "Above cohort" panel: top 3 signal strengths from `signal_ranking.strengths` (signal label, your value, cohort mean, Z-score badge).
- "Below cohort" panel: top 3 signal weaknesses.
- Note when cohort_size < 10: "Not yet enough peer data to compute a percentile."

Backed by `GET /api/v1/portal/entities/{id}/peers`.

### Page: `/actions`

- Headline: "Prioritised actions to improve your score."
- Ordered list of `RemediationAction`s from `GET /api/v1/portal/entities/{id}/actions`.
- Each action card shows:
  - Headline (bold).
  - Description.
  - Effort badge (LOW/MEDIUM/HIGH with color).
  - Typical duration and cost.
  - Estimated premium reduction in dollars and percent.
  - "Would change tier" badge (if `would_change_tier=True`).
  - "Evidence required" callout.
- Placeholder actions visually distinguished (italic, lighter, "Generic guidance" tag).
- Footer: "X signals need remediation guidance authored" if placeholder_count > 0 — visible to brokers only (helps Marsh sell improvement).

### Page: `/submissions`

List view: all submissions for the current entity (CLIENT) or all submissions for clients in the book (BROKER).

Columns: entity name (BROKER only), coverage, status badge, quote score, tier, premium, last updated, referral state.

Row click → `/submissions/{id}`.

### Page: `/submissions/[id]`

Submission detail. The deepest page in the portal — **this is the Act 7 page**.

- Header: entity, coverage, status, score, tier, premium.
- **Quote evolution timeline**: if this submission has multiple quotes (re-assessments from Phase 5), show them in chronological order with score/tier/premium deltas. The visual narrative of "Marsh saved you $X."
- **Referral panel**: state, open query (if any), message thread.
- For BROKER viewing: reply form (Phase 5 reply endpoint) when state is `AWAITING_BROKER`.
- For CLIENT viewing: read-only thread.
- Bottom: top 3 next actions from the remediation plan ("Here's what to address next").

The quote evolution timeline is the demo's emotional moment. It needs to be visually obvious that the score went up and premium came down because of Marsh's reply.

### Page: `/queries`

Broker-only. Client gets redirected to `/overview` if accessed.

- List of open queries from `GET /api/v1/portal/queries`.
- Each row: client name, coverage, query body excerpt, signal evidence requested, age of query.
- Row click → `/submissions/{id}` with the reply form pre-focused.

### Carrier-side additions

The carrier UI already renders referrals. Add a small affordance on the referral detail view (location: `frontend/src/components/submissions/content/risk_terms/...` or wherever referrals render — confirm in discovery):

- **"Raise query" button** when referral state is `IN_REVIEW` or `PENDING`.
- Opens a modal: free-text body, optional signal selector (drop-down of the coverage's signals).
- Submits to `POST /api/v1/referrals/{id}/messages` (Phase 5).
- After submit, modal closes and referral row updates to show `AWAITING_BROKER` state.

This is the carrier-side counterpart to the broker's reply form. Without it, Act 4 has nowhere to happen.

### Component reuse

- Cards: `frontend/src/components/base/cards.tsx`
- Modal: `frontend/src/components/base/modal.tsx`
- Charts (bell-curve, bar chart): extend `frontend/src/components/base/charts/primatives.tsx`
- Key details bar: `frontend/src/components/base/keyDetailsBar.tsx`

New portal-specific components:

```
frontend/src/components/portal/
  PortalNav.tsx
  ClientBookTable.tsx         # broker overview table
  ClientOverviewCard.tsx      # client overview card
  StrengthDragPanel.tsx       # used on /score
  PremiumWaterfall.tsx        # used on /score
  CohortBellCurve.tsx         # used on /peers
  PeerSignalPanel.tsx         # used on /peers
  ActionCard.tsx              # used on /actions
  QuoteEvolutionTimeline.tsx  # used on /submissions/[id] — THE Act 7 moment
  ReferralThread.tsx          # used on /submissions/[id]
  BrokerReplyForm.tsx         # used on /submissions/[id] for BROKER
  RaiseQueryModal.tsx         # used on carrier-side referral view
```

Each component <250 lines. If one grows past that, extract subcomponents.

### Data fetching

Match the existing pattern. If carrier app uses SWR, portal uses SWR. If React Query, same. If raw fetch + useEffect, same. **Confirm during discovery** — do not introduce a new pattern.

Define a `frontend/src/lib/portal/api.ts` with typed helper functions:

```ts
export async function fetchOverview(): Promise<OverviewResponse> { ... }
export async function fetchEntityScore(entityId: number): Promise<EntityScoreResponse> { ... }
export async function fetchEntityPeers(entityId: number): Promise<EntityPeersResponse> { ... }
export async function fetchEntityActions(entityId: number): Promise<EntityActionsResponse> { ... }
export async function fetchEntitySubmissions(entityId: number): Promise<EntitySubmissionsResponse> { ... }
export async function fetchBrokerQueries(): Promise<BrokerQueriesResponse> { ... }
export async function createSubmission(entityId: number, payload: SubmissionCreatePayload): Promise<{ submission_id: number }> { ... }
export async function replyToQuery(referralId: number, payload: ReplyPayload): Promise<ReplyResponse> { ... }
```

Types live in `frontend/src/types/portal.ts`, mirroring Phase 6 Pydantic schemas.

### Visual design

- Reuse `theme.css` tokens (`generate-*`).
- Strength color: `var(--generate-text-good)`.
- Drag color: `var(--generate-text-bad)`.
- Neutral: `var(--generate-text-maybe)`.
- Effort badges: LOW=green, MEDIUM=amber, HIGH=red.
- Tier badges reuse existing tier color conventions from the carrier UI — discover and reuse.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Exact data-fetching pattern (SWR / React Query / raw fetch).
2. Exact location of referral rendering in the carrier UI (to add the Raise Query affordance).
3. The existing `(carrier)/` group does NOT already exist — Phase 8 creates the route group split. Verify with `ls src/app/`.
4. Whether the login page is already outside any group or needs to be moved out.
5. Tier color conventions.

### Step 2: Route group split

Move existing routes under `src/app/(carrier)/`. This is a directory move; URLs unchanged. Update any internal `import` paths that reference old locations.

Test the carrier app still works end-to-end after the move.

### Step 3: Portal scaffolding

Create `src/app/(portal)/layout.tsx` with `SessionGuard`, top bar, and `PortalNav`.

Create `PortalNav.tsx` with role-aware items.

### Step 4: API client

Create `frontend/src/lib/portal/api.ts` and `frontend/src/types/portal.ts`. Type every endpoint per Phase 6's schemas.

### Step 5: Build pages bottom-up

Build in this order so each page can be smoke-tested against demo seed data as soon as it's complete:

1. `/overview` (broker view): list clients from `/portal/overview`.
2. `/overview` (client view): same endpoint, different render branch.
3. `/score`: build `StrengthDragPanel`, `PremiumWaterfall`, render impact breakdown.
4. `/peers`: build `CohortBellCurve`, `PeerSignalPanel`.
5. `/actions`: build `ActionCard`, render remediation plan.
6. `/submissions`: list view.
7. `/submissions/[id]`: build `QuoteEvolutionTimeline`, `ReferralThread`, `BrokerReplyForm`.
8. `/queries`: broker inbox view.

After each page, hit it manually in the browser using the demo seed user credentials.

### Step 6: Carrier-side Raise Query affordance

Add `RaiseQueryModal.tsx` and wire it into the referral detail view. Test that it correctly transitions a referral to `AWAITING_BROKER`.

### Step 7: Login redirect

Update `src/app/login/page.tsx` post-login logic to route by role.

### Step 8: Manual seven-act walkthrough

With `python -m seed demo-reset` run, walk all seven acts in the browser:

1. Log in as `client.acme@demo.dsi`. Verify `/overview`, `/score`, `/peers`, `/actions` render correctly.
2. Click "Request renewal" → submission created.
3. Log out, log in as `underwriter.demo@demo.dsi`. Verify Acme appears in referral queue.
4. Open the referral, click "Raise query", submit MFA query. Verify state → `AWAITING_BROKER`.
5. Log out, log in as `marsh.admin@demo.dsi`. Verify `/queries` shows Acme's query. Open `/submissions/{id}`, reply with MFA evidence + signal update. Verify reassessment triggered.
6. Log out, log in as `underwriter.demo@demo.dsi`. Verify Acme's new quote at higher score / lower premium.
7. Log out, log in as `client.acme@demo.dsi`. Verify `/submissions/{id}` shows the quote evolution timeline with the delta narrative.

**This walkthrough is the acceptance gate.** If any act doesn't work in the browser, Phase 8 is not done.

### Step 9: Tests

Component tests (where the existing frontend has a testing harness):

- `PortalNav` renders different items by role.
- `StrengthDragPanel` renders strengths/drags correctly.
- `ActionCard` renders effort badge correctly.
- `QuoteEvolutionTimeline` renders multiple quotes in order.

End-to-end test (if Playwright/Cypress harness exists):
- Automate the seven-act walkthrough.

If no E2E harness exists today, document the manual walkthrough in `development/project/version/8/demo_walkthrough.md` as the canonical test script.

## Constraints & Principles

1. **Single phase, single integration pass.** No backend changes during Phase 8. Backend gaps → v8.1.
2. **Reuse before invent.** Base components, charts, theme tokens — reuse what exists. Add new only when no existing primitive fits.
3. **Carrier app untouched** except for the Raise Query affordance and the route group rename. No incidental refactors.
4. **Type contracts.** All portal API responses typed in `frontend/src/types/portal.ts`. No `any` shortcuts.
5. **Demo passes the seven-act walkthrough.** This is the gate, not unit tests alone.
6. **Mobile-friendliness deferred.** Portal targets desktop browser for the Marsh demo. Responsive design is v8.1.
7. **Accessibility baseline.** Keyboard navigable, semantic HTML, alt text. No full WCAG audit in v8.
8. **Performance.** Each page loads in <500ms against demo seed data. No lazy loading needed at this scale.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Route group split breaks existing routes | Step 2 ends with smoke-test of the carrier app. Roll back if broken. |
| Data fetching pattern in carrier app is undocumented | Discovery step 1 confirms. |
| QuoteEvolutionTimeline doesn't have enough data to render (e.g. only one quote at Act 7) | Phase 7 seed ensures Acme has two quotes by end of demo (initial + post-reply re-assessment). Verify in smoke test. |
| Bell-curve chart for cohort distribution is non-trivial | Use existing chart primitives + a custom marker. If existing primitives can't render a kernel-density curve, fall back to a histogram. Both visually convey "where you are in the distribution." |
| Carrier-side referral view location unclear | Discovery step confirms. If the existing path can't accept a small affordance, ask before refactoring carrier UI. |
| Portal nav and carrier nav diverge in style, looking unbranded | Reuse the existing nav primitives (NavGroup per recent recon notes). Same tokens, same shell — different nav items. |
| Auth guard interacts oddly with route groups | Each route group has its own layout with its own SessionGuard call. Root layout does not gate. |

## Dependencies

- **Phases 1–7 complete.** Backend is the gate.
- Demo seed runnable via `python -m seed demo-reset`.
- Frontend `Role` enum includes `BROKER` and `CLIENT` (Phase 1 already did this).

## Success Criteria

1. Route groups `src/app/(carrier)/` and `src/app/(portal)/` exist. Existing carrier routes function unchanged.
2. Five portal pages live and render against demo seed data: `/overview`, `/score`, `/peers`, `/actions`, `/submissions` (list + detail). Broker-only `/queries`.
3. Login redirect routes BROKER and CLIENT to `/overview`, other roles to carrier dashboard.
4. Carrier-side referral view has "Raise query" affordance that transitions referrals to `AWAITING_BROKER`.
5. Broker can reply to a query with a signal value update, triggering re-assessment.
6. Quote evolution timeline visible on `/submissions/[id]` after re-assessment.
7. **The seven-act manual walkthrough (Step 8) completes without errors against `python -m seed demo-reset` state.**
8. Existing carrier-side tests still pass.
9. New component tests pass (if harness exists).
10. `python -m seed demo-reset` + manual walkthrough together complete in <2 minutes wall clock for a single demo run.
11. No backend changes, no schema changes, no seed changes.

## Out of Scope (Phase 8)

- Mobile / responsive design.
- WCAG full audit.
- Notification UI (toast / inbox unread badges with live updates).
- Multi-coverage views (cyber only in v8).
- Admin pages within the portal.
- Self-service password management within the portal (existing reset-password flow used).
- Embedded payments / binding.
- Marketing site / landing page.
- Theming per broker (white-label).
- Internationalisation.
