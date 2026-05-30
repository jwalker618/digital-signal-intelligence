# Version 9 — Phase G: Mobile Companion

**Status:** G.0–G.4 SHIPPED — see check-marks below
**Branch:** `claude/nice-ride-xSz7t`
**Source of truth:** `development/project/version/9/Digital Signal Intelligence - mobile.zip`
(extract to `/tmp/dsi-mobile/`; canonical assets in `mobile/`)

## Purpose
Ship a dedicated mobile surface — a single continuous **intelligence feed**
per persona, no tab bar, optimised for a one-handed phone. The desktop app
stays unchanged. The phone version is the "ambient" companion: glanceable
score, what's awaiting you, conversations, signal feed, and an Ask pill.

## Template anatomy (`mobile/app.jsx` + `widgets.jsx` + `mobile.css`)
1. **Glass header** (sticky, blurred) — org avatar, greeting, org name, dark toggle, persona segment (broker/client/carrier).
2. **Climate strip** — small tone dot + "BOOK CLIMATE · Strong" type line.
3. **Brief** — one-sentence morning briefing with bolded entities.
4. **Signal hero card** — 124px ring + sparkline + delta pill + caption + 2 movers list.
5. **Awaiting you rail** — horizontal snap cards (coral spine, 79% width), CTA button.
6. **At a glance** — 2×2 grid of iOS-widget tiles (one can be a tier-mix mini chart).
7. **Conversations** — thread list (avatar, who, sub, ask preview, tone chip).
8. **Signal feed** — vertical timeline with icon rail.
9. **Floating Ask pill** — bottom dock, "Ask anything about your book…" + send.
10. **Bottom sheet** — opens on thread or awaiting tap (header + bubbles + smart-reply prefill + composer).

## Working method
1. Mobile lives at **`/m`** as a single page (no tabs). All persona switching is in-page state.
2. **Tokens already align** — `globals.css` exposes the `--color-*` family the template references as `--canvas`, `--surface`, etc. We add aliases (or use `--color-*` names) and the mobile-specific helpers.
3. **Real data via existing fetches** (`fetchBookOverview` etc.) — the desktop store is the source of truth; we just project it to the feed shape.
4. Use iconify-icon via the Iconify React shim or inline SVG-from-lucide-react.
5. Tailwind for layout; raw CSS file (`mobile.css`) for the dense animation + glass-blur rules that don't translate cleanly to utility classes.
6. **Auto-redirect mobile viewports** from `/` and persona roots to `/m` (with a `?desktop=1` opt-out persisted in localStorage).
7. Commit per phase with a session URL.

## PHASE G.0 — Foundation
- [x] Add `mobile.css` (lifted from template, scoped under `.dsi-mobile`,
      rewritten to reference the existing `--color-*` tokens directly).
- [x] Create `app/m/layout.tsx` (SessionGuard + mobile-only shell, no
      desktop sidebar/topbar). Added `/m` to SessionGuard's
      persona-agnostic allow-list so role-vs-path doesn't bounce mobile.
- [x] Create `app/m/page.tsx`.
- [x] Add `viewport` export to root layout (`viewport-fit: cover`,
      `user-scalable: false`).

## PHASE G.1 — Primitives (`components/mobile/primitives.tsx`)
- [x] `Section` — h3 + optional link.
- [x] `Chip` — tone-mapped pill.
- [x] `Sparkline` — 14-point inline SVG with gradient fill.
- [x] `SignalRing` — 124px arc, animated stroke-dasharray.
- [x] `TONE_BG / TONE_FG / TONE_BASE` maps + `avatarColor` hash.
- [x] Icons inlined via `lucide-react` (no iconify dependency).

## PHASE G.2 — Feed sections
- [x] `SignalHero` (ring + delta + sparkline + movers).
- [x] `AwaitingRail` (horizontal snap, coral spine, CTA).
- [x] `GlanceGrid` + `TierMix` (2×2 widget tiles).
- [x] `ThreadList` (avatar + tone chip + ask preview).
- [x] `SignalFeed` (timeline with icon rail).
- [x] `ReplySheet` (bottom sheet + smart-reply pre-fill + composer).
- [x] `React.memo` on `ThreadRow`, `FeedEvent`, `GlanceTile`, `Chip`,
      `Sparkline`, `AwaitingRail`, `SignalHero`.

## PHASE G.3 — Data adapter (`lib/mobileFeed.ts`)
- [x] `buildBrokerFeed(BrokerOverviewResponse, userName)` — projects
      desktop /portal/overview payload to the mobile feed shape.
- [x] `buildClientFeed(ClientOverviewResponse, userName)` — same for
      the client surface, with renewal-days + percentile.
- [x] `buildCarrierFeed(submissions, userName)` — reads the
      `/frontend/pipeline` payload, derives referred/cleared counts.
- [x] Honesty rule: empty arrays + "—" placeholders when fields are
      genuinely missing.
- [x] `MobileApp` orchestrator: parallel persona fetches, persona seg
      gated by user role.

## PHASE G.4 — Viewport routing
- [x] `app/page.tsx` — coarse-pointer / `max-width: 640px` → `/m`.
- [x] `(app)/layout.tsx` mounts `<MobileRedirect />` so direct hits to
      `/broker` etc. also redirect on phones.
- [x] `?desktop=1` opt-out persists `dsi-prefers-desktop` in
      localStorage; "View on desktop →" link at feed footer reverses.

## PHASE G.5 — Polish (DEFERRED)
- [ ] Lazy-load `ReplySheet` via `next/dynamic` (currently always mounted).
- [ ] Drag-to-dismiss on bottom sheet.
- [ ] Real composer wired through to `/portal/queries` reply endpoint
      (currently smart-reply is a UX-only flash).
- [ ] Bind Ask pill to a backend chat endpoint when one lands.
- [ ] PWA manifest + icon set so the mobile feed installs to home screen.

## File map (mobile)
| Template file | Implementation |
|---|---|
| mobile/app.jsx | app/m/page.tsx + components/mobile/MobileApp.tsx |
| mobile/widgets.jsx | components/mobile/{Section,SignalHero,AwaitingRail,GlanceGrid,ThreadList,SignalFeed,Chip,Sparkline,SignalRing}.tsx |
| mobile/feed_data.js | lib/mobileFeed.ts |
| mobile/mobile.css | app/m/mobile.css |
| mobile/tokens.css | already covered by app/globals.css |
