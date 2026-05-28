# DSI Frontend

Next.js 16 / React 19 / Tailwind 4 rebuild of the DSI portals against the
reimagined design system. Replaces the previous `frontend/` in the main
monorepo.

## Status

**Phase 1 — Client persona — landed.**

| Surface | Endpoint(s) | State |
|---|---|---|
| Foundation (tokens, primitives, charts, chrome) | — | ✅ |
| `/login`, `/login/sso`, `/login/mfa`, `/login/reset-password`, `/login/reset-password/set` | `/api/v1/auth/*` | ✅ wired to `authStore` |
| `/profile` (account) | `useAuthStore` only | ✅ |
| `/client` Overview | `GET /portal/overview` | ✅ |
| `/client/profile` | `GET /portal/profile` | ✅ |
| `/client/coverages` | `GET /portal/overview` | ✅ |
| `/client/submissions/[code]` | `GET /portal/submissions/{code}` + `/score` | ✅ |
| `/client/drivers` | `GET /portal/submissions/{code}/score` | ✅ |
| `/client/peers` | `GET /portal/submissions/{code}/peers` | ✅ |
| `/client/actions` | `GET /portal/submissions/{code}/actions` | ✅ |
| `/client/scenarios` | `GET /portal/submissions/{code}/score` (client-side projection) | ✅ |
| `/client/request` | `POST /portal/coverage-requests` | ✅ |
| `/client/communications` + thread | `GET /portal/communications`, `POST /portal/queries/{ref}/reply` | ✅ |
| `(app)` group wrapped in `SessionGuard` | — | ✅ |
| `/broker` Book of Clients | `GET /portal/overview` (broker) | ✅ |
| `/broker/client-health` | `GET /portal/client-health` | ✅ |
| `/broker/coverages` | `GET /portal/overview` | ✅ |
| `/broker/placement` | `GET /portal/placement/{code}` | ✅ |
| `/broker/carriers` | `GET /portal/carriers` | ✅ |
| `/broker/recommendations` | `GET /portal/recommendations`, `POST /portal/recommendations/send` | ✅ |
| `/broker/communications` + thread | shared `ThreadView` w/ client | ✅ |
| `/broker/market` | `GET /portal/market/pulse` | ✅ |
| `/broker/aggregation` | `GET /portal/aggregation` | ✅ |
| `/broker/book-health` | `GET /portal/book-health` | ✅ |
| `/carrier` Referral Pipeline | `GET /api/v1/frontend/pipeline` (dsiStore) | ✅ |
| `/carrier/pipeline` Full Pipeline | dsiStore (filter mode) | ✅ |
| `/carrier/metrics` Performance Metrics | dsiStore aggregates | ✅ |
| `/carrier/world-engine` | `GET /api/v1/world-engine/{stats,drift-alerts,relationships}` | ✅ |
| `/carrier/submissions/[code]` Workbench layout + Summary | dsiStore.fetchCoreSubmissionDetail | ✅ |
| Workbench: Pricing Anatomy | activeVersion modifier chain | ✅ real |
| Workbench: Risk Assessment | activeVersion.signal_conditions + fetchRiskSignals | ✅ real |
| Workbench: Model Versions | dsiStore.fetchHistory | ✅ real |
| Workbench: Terms Overview | activeCommercial + activeVersion | ✅ |
| Workbench: Premium Assembly | activeVersion modifier chain (narrative) | ✅ |
| Workbench: Distribution | activeCommercial.commercial_distribution | ✅ |
| Workbench: Deductible Structure | activeRisk.deductible_bands + activeVersion.final_premium_detail | ✅ |
| Workbench: Coverage Terms | activeRisk (sub-limits + endorsements) | ✅ |
| Workbench: SIR & Waiting Periods | activeRisk.sir / waiting_periods | ✅ |
| Workbench: Aggregate & Reinstatement | activeRisk.aggregate_limit / reinstatements | ✅ |
| Workbench: Loss Assessment | dsiStore.fetchLossAnalytics + activeVersion loss fields | ✅ |
| Workbench: Exposure Assessment | dsiStore.fetchExposureAnalytics + activeVersion exposure fields | ✅ |
| Workbench: Scenarios | scenarioEngine.runFullCascade (interactive) | ✅ |
| Workbench: Referral Actions | postBrokerReply + signal_value_update | ✅ |
| `/admin` System Health | `GET /api/v1/admin/health[/pipeline,/extractors]` | ✅ |
| `/admin/configs` | `GET /api/v1/admin/configs`, `POST .../versions/{id}/{transition}` | ✅ |
| `/admin/users` | `GET /api/v1/admin/users`, `/admin/roles`, `POST /admin/users/{id}/deactivate`, `/admin/users/invite` | ✅ |
| `/admin/audit` | `GET /api/v1/admin/audit`, `GET /admin/audit/export` | ✅ |
| `/admin/losses` | `GET /api/v1/losses`, `POST /losses/import`, `POST /losses/link-all` | ✅ |
| `/admin/recalibration` + `/[id]` | `GET /api/v1/recalibration/proposals[/{id}]`, `POST .../{approve,reject,deploy}` | ✅ |

## Architecture

```
src/
├── app/                            # Next.js App Router
│   ├── login/                      # Auth surfaces (login, SSO, MFA, reset)
│   ├── (app)/                      # Authed shell — sidebar + topbar
│   │   ├── client/                 # Client persona routes
│   │   └── profile/                # Account page (no persona)
│   ├── globals.css                 # Tailwind 4 @theme tokens + dark mode
│   └── layout.tsx                  # Pre-hydration theme boot + fonts
├── components/
│   ├── ui/                         # cva primitives — Card, Chip, Button,
│   │                                 Eyebrow, NumDisplay, ScoreBar, KPITile
│   ├── chrome/                     # PersonaSidebar, Topbar, AuthBrandPanel
│   ├── charts/                     # Sparkline, ScoreHistory, CohortBar,
│   │                                 PremiumBreakdown, Waterfall, BellCurve
│   ├── base/                       # PageLoading/Error/RoleGate, ComingSoon
│   ├── auth/                       # SessionGuard, MFASetup, MFAVerify  ← lifted
│   ├── shared/                     # NotificationToast, PermissionGate  ← lifted
│   └── layout/navConfig.ts         # Per-persona nav + permissions  ← lifted
├── lib/                            # ← Mostly lifted verbatim from existing app
│   ├── api.ts, authApi.ts, portalApi.ts
│   ├── useRoleScopedFetch.ts       # The canonical data-fetch hook
│   ├── format.ts, portalTone.ts, portalPaths.ts
│   ├── scenarioEngine.ts, shockEngine.ts
│   ├── websocket.ts, push.ts
│   └── utils.ts                    # +cn() helper for cva
├── store/                          # ← Lifted verbatim
│   ├── authStore.ts                # zustand, MFA + SSO + refresh + permissions
│   ├── dsiStore.ts                 # navigation / page-action slots
│   └── themeStore.ts               # dark mode persistence
└── types/                          # ← Lifted; codegen target in follow-up
    ├── portal.ts                   # 520 LOC mirror of FastAPI Pydantic
    ├── auth.ts, dsi.ts, admin.ts, recalibration.ts, worldEngine.ts
    └── (api.ts)                    # ← Will be openapi-typescript output
```

## Conventions

### Design tokens (Tailwind 4 CSS-first)

All design tokens live in `src/app/globals.css` as CSS custom properties
under `@theme` (light) and `.dark { … }` (dark override). Tailwind 4
auto-derives utilities: `--color-canvas` → `bg-canvas`, `text-canvas`,
`border-canvas`. No `tailwind.config.ts`.

Three semantic accent roles:

- **`info`** (teal) — informative hero facts (score, premium, percentile)
- **`spot`** (coral) — awaiting-you / urgent action / opportunities
- **`pos`** / **`neg`** / **`warn`** — strengths / drags / caution
- **`aux`** (blue) — secondary informative (exposure, cohort)

### Data hooks

Every page fetches via `useRoleScopedFetch`. The hook owns loading/error/
gating; pages render `<PageLoading />` / `<PageError />` / `<RoleGate />`
from `@/components/base/pageStates`.

```tsx
const { accessToken, user } = useAuthStore(...);
const enabled = !!accessToken && user?.role === "CLIENT";
const { data, error, loading } = useRoleScopedFetch({
  fetcher: () => fetchOverview(accessToken),
  enabled,
  deps: [accessToken],
});
```

### Types

Today: hand-maintained TS mirror at `src/types/portal.ts` mirrors the
FastAPI Pydantic models. **Tomorrow**: run `npm run gen:types` to overwrite
`src/types/api.ts` with `openapi-typescript` output. Page imports continue
to use named exports — switch the source file when codegen lands.

## Getting started

```sh
cp .env.example .env.local       # adjust NEXT_PUBLIC_API_URL if needed
npm install
npm run dev                      # http://localhost:3000
```

The backend must be reachable on `http://localhost:8000` — `next.config.ts`
rewrites `/api/v1/*` to that host. Seed it once before the first run:

```sh
# From the monorepo root (one level above frontend/)
python -m seed demo-reset
# starts FastAPI + populates Postgres with the demo state
```

### Smoke-test path

Walk all four personas in one session — every route should load real data
(or show a calm empty-state if the backend didn't seed that area).

1. **Sign in** at `/login`
   - Use a demo user from `python -m seed demo-reset` output
   - SSO via `/login/sso`, MFA via `/login/mfa`, reset via `/login/reset-password`
2. **Root** `/` redirects you to the right persona based on `user.role`
3. **Client persona** (CLIENT role):
   - `/client` shows your active coverages, primary in a teal hero card
   - Click a coverage → `/client/submissions/{code}` (composite + impact)
   - Sidebar tour: Profile / Coverages / Risk Insights / Benchmarks / Scenarios / Action Plan / Request Coverage / Communications
   - Open an Awaiting-you thread → reply composer fires `POST /portal/queries/{ref}/reply`
4. **Broker persona** (BROKER role):
   - `/broker` shows your book grouped by client
   - Sidebar: Client Health (engagement score, opportunity/risk flags) /
     Coverages (sortable book) / Placement (carrier-fit ranked) /
     Carriers / Recommendations (cross-sell modal sends `POST /portal/recommendations/send`) /
     Communications / Market / Aggregation / Book Health
5. **Carrier persona** (UNDERWRITER / ADMIN / etc):
   - `/carrier` referral pipeline
   - `/carrier/world-engine` — maturity ladder + drift alerts (Ack button posts to `/world-engine/drift-alerts/{id}/acknowledge`)
   - `/carrier/metrics` — auto-approve rate + decision mix + coverage mix
   - Click any submission → `/carrier/submissions/{code}` — 15-tab Workbench
   - Workbench tabs of note:
     - **Pricing Anatomy** — modifier chain waterfall + signal conditions
     - **Risk Assessment** — signals grouped by action
     - **Premium Assembly** — vertical step-by-step narrative
     - **Scenarios** — drag signal sliders + limit/deductible; runs `scenarioEngine.runFullCascade` live
     - **Referral Actions** — reply composer with optional signal_value_update
6. **Admin console** (ADMIN role, requires `admin:system`):
   - `/admin` — system status + extractor table
   - `/admin/configs` — promote draft → validate → calibrate → deploy
   - `/admin/users` — table + Invite modal
   - `/admin/audit` — filterable event log + CSV export
   - `/admin/losses` — Loss Register; import CSV via the file picker, link via the button
   - `/admin/recalibration` → `/{id}` — review weight + tier changes, approve/reject/deploy

### What to look for

- **Theme toggle** in every topbar — confirm tokens swap correctly (no flash on hydration; the pre-hydration script in `app/layout.tsx` reads the persisted store)
- **SessionGuard** — sign out and visit `/client` directly; should bounce to `/login?next=...`
- **Persona bounce** — sign in as CLIENT and try to load `/broker` — SessionGuard redirects you to `/client`
- **PermissionGate** — admin sub-pages refuse to render content without the matching permission and show a clean error card
- **Empty states** — every page has a sensible "no data" branch; the loose-typed workbench tabs gracefully render "—" instead of crashing on missing fields

## What I left in place from the existing app

Lifted verbatim (no API/contract changes):
- `lib/{api,authApi,portalApi,format,portalTone,portalPaths,scenarioEngine,shockEngine,websocket,push,useRoleScopedFetch,keytermPalette,chartConfig}.ts`
- `store/{authStore,dsiStore,themeStore}.ts`
- `types/*.ts`
- `components/auth/{SessionGuard,MFASetup,MFAVerify}.tsx`
- `components/shared/{PermissionGate,NotificationToast,PendingQueryRow}.tsx`
- `components/layout/navConfig.ts`
- `next.config.ts`, `postcss.config.mjs`, `eslint.config.mjs`
- `public/{custom-sw.js,manifest.json,…}`

Restyled (same API, new visual treatment):
- `components/base/pageStates.tsx`

## What's next

1. **Smoke-test against a running backend.** `python -m seed demo-reset` upstream, `npm run dev` here. Verify every fetch wires to a real response.
2. **Run `npm run gen:types`** to replace the manual `types/portal.ts` mirror with codegen output. Drop in once you have an OpenAPI URL or file.
3. **Phase 2 — Broker portal.** 10 routes; can reuse most primitives. `useRoleScopedFetch` patterns carry over.
4. **Phase 3 — Carrier portal + 15-tab Submission Workbench.** Heaviest pass — needs the drill-down sidebar mode from `DRILL_DOWN_CATEGORIES` and the lifted `dsiStore.activeSubmission` state.
5. **Phase 4 — Admin console** (7 routes).

## Known gaps / decisions to revisit

- **Submission detail tabs.** Current page renders Summary + Score + Impact + Quote History on one scroll. The design's tabbed layout (Summary / Drivers / Peers / Actions / Quote / Comms) was reduced to drill-down tiles linking to the persona-level pages with `?code=`. That avoids deep nesting and reuses the persona pages, but if the team prefers proper tabs we can wire them via `app/(app)/client/submissions/[code]/[tab]/page.tsx`.
- **Bell-curve SD.** `/peers` doesn't return a cohort standard deviation today; I hardcode `sd = 80` to draw a plausible distribution. If the backend can surface it (or top-decile + median + range), I'll wire that through.
- **Scenarios projection** is a simple sum of captured-drag deltas. Real scenarios need the full `scenarioEngine.runFullCascade`, which is wired but requires `signals[]` + `activeVersion` that the portal API doesn't yet return — needs a `/portal/submissions/{code}/scenario-context` endpoint.
- **Coverage book detail (carrier, limit, retention, renewal).** `/portal/overview` returns only score/premium/tier/percentile. The Coverages table shows what's available; adding the rich policy fields needs backend work or composing with a new endpoint.
