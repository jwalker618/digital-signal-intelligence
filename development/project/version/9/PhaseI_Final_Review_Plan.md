# Version 9 — Phase I+: Final-Review Resolution Plan (post-3103 + docx)

**Status:** EXECUTING
**Branch:** `claude/nice-ride-xSz7t`
**Sources of truth:**
- `development/project/version/9/3103/Digital Signal Intelligence.zip` → extracted to `/tmp/dsi-3103/`
- `development/project/version/9/3103/Final front-end review.docx` → text extracted in chat
- Revised pack (still authoritative for unchanged surfaces): `/tmp/dsi-revised/`

## Decisions baked in (no need to re-ask)
- **Sidebar open behaviour: hover-only.** Click-to-pin removed; the toggle button stays for keyboard a11y but the panel opens on hover with the existing 150/300ms enter/leave delays.
- **Seed richness: regenerate.** Phase M does ONE backend reseed pass so most submissions carry the full MV chain (multiple model versions, signal/loss/exposure adjustments, populated cohort + signal-audit) and lights up the four "looks placeholder" complaints together.
- **Provenance: per-page data legend.** Small `i` affordance per page (or per card where it varies); opens a legend keyed to four tokens — `live DSI signal · derived · seed/sample · placeholder`. No mapping doc.
- **Broker Coverages carrier column:** sourced from `CommercialTermsRecord.carrier_name` (already used in the broker Client Workbench endpoint). Reseed will populate it where missing. Reverses my Phase H "no source" deferral now that you've directly overruled it.

## Working method
1. Each cohort is independently shippable; commit per cohort (item count permitting).
2. Retain all Phase F–H performance patterns (`useEnsureFetched`, `React.memo`, fetch-once-via-context, `optimizePackageImports`).
3. Honesty rule still applies for items NOT covered by Phase M (don't fabricate). After Phase M most "looks-placeholder" complaints are resolved by real data.
4. **No duplication of Phase F/G/H work.** Items already shipped (chrome chrome, carrier crash fix, fill-width margins, ReimPeers rebuild) are noted as carry-forward; only deltas land here.
5. AST-parse all Python edits (`python3 -c "import ast; ast.parse(...)"`); read TSX edits carefully (no `node_modules` in env).

---

## COHORT I — Global chrome + blockers
1. **[Blocker] Investigate + fix Broker Workbench load error.** Reproduce; likely a Pydantic-schema/attribute mismatch like the `recommended_limit` crash. Until cleared, Cohort K's Broker Workbench items are unreachable.
2. **Sidebar: hover-only.** Remove the click-to-pin path; toggle button stays for keyboard a11y. Same component, persona-sidebar.tsx.
3. **Sidebar nav stability on expand.** Nav items must NOT shift vertically when the panel opens. Reserve the same per-item geometry in both states.
4. **Workbench sidebar variance.** Remove the user identity + submission reference from the top of the carrier `WorkbenchShell` sidebar; eliminate the inner scrollbar. Sidebar must be icons-only, identical in placement to the persona sidebar.
5. **Title/first-card de-dup sweep.** Where the topbar crumb equals the first analysis-area heading, drop the heading. Audit + apply.
6. **Pipeline summary currency formatting.** `$14448k` → `compactCurrency` so values render as `$14.4M` etc.

## COHORT J — README surgical (in README's suggested order)
- **J1 — Change #3: Book of Clients layout.** Two-column work area (roster left, internal-scroll, sticky head + sticky thead; Tier mix + Open queries pinned right at ~392px). All existing filters/search retained.
- **J2 — Change #2: Coverage Detail + Profile softening.**
  - New route `app/(app)/client/coverages/[code]/page.tsx` with the prototype's `ReimCoverageDetail` structure (header band, KPI strip, terms, placement timeline, premium snapshot, loss+exposure reusing existing `_components`, awaiting/green state, documents, contacts). No submission chrome.
  - `client/coverages` `PolicyRow` now links here, NOT `client/submissions/{code}`.
  - `client/profile`: drop per-row chevrons; add the "Open any line in Coverages for its full policy record" hint.
- **J3 — Change #1: Multi-coverage switcher + 5 pages.**
  - Build `src/components/portal/CoverageSwitcher.tsx` (segmented `[ All · Cyber · PI · D&O ]` with overflow + count badge + status dot) and `PageHead` wrapper. Drives off `?code=`; `code=all` = portfolio.
  - Roll onto Summary, Risk Insights (replace the bare `<select>`), Industry Benchmarks, Scenarios, Action Plan.
  - Per-page roll-up math + per-line specifics per README spec. The "practices that drive your peers' scores" block returns as part of Industry Benchmarks' per-line view (uses peer-practice adoption data — depends on Phase M to populate cohort signal coverage).

## COHORT K — Docx-only page-level fixes (no template change implied)
- **Overview** (`client/page.tsx`)
  - Your Signal Score chart: Y-axis truncated to "9997" + non-rounded score — chart axis bug; fix axis domain + value rendering.
  - "Standard Tier" / "64th percentile" — investigate semantics; if wording is wrong, correct.
  - Annual Premium chart: render top-3 split, not a single bar.
- **Request Coverage** (`client/request/page.tsx`)
  - Indicative range gated behind a coverage having been selected.
  - Coverage line list sourced from DSI `config.yamls` (the existing coverage configurations) not a hard-coded list.
- **Broker Coverages** (`broker/coverages/page.tsx`)
  - Add Carrier column from `CommercialTermsRecord.carrier_name`. Type extension + builder change.
- **Broker Client Health** (`broker/client-health/page.tsx`)
  - Surface quiet-client alerts properly (currently hidden); engagement scoring freshness check (rebuild on real recency).
- **Broker Market Pulse** (`broker/market/page.tsx`)
  - Loss events sourced from DSI (loss store) rather than placeholder.
- **Carrier Workbench Summary** (`carrier/submissions/[code]/summary/page.tsx`)
  - Scroll: fix vertical overflow so the tab body is fully scrollable.
  - Decision section restored to template structure.
  - Three-pillar (Signal/Loss/Exposure): top contributory signal groups must render the actual `group_id · weight · contribution` rows we already compute. Loss + Exposure parallel.
  - "Who are they" / Commercial / Risk summaries: align fields with the latest assessment payload + the discovery output; "Who are they" must show entity discovery facts.
- **Carrier Workbench Pricing Anatomy** (`carrier/submissions/[code]/pricing/page.tsx`)
  - Signal / Direct query / Loss / Exposure adjustments visible for the majority of submissions (mostly a seed-richness item — Phase M).
  - Recommended options: "Select" button creates a new model version pinned to that option.
- **Carrier Workbench Risk Assessment** (`carrier/submissions/[code]/risk/page.tsx`)
  - Group & Signal breakdown must include weight + score columns + allow row drill-down to child signals.
- **Carrier Workbench Loss Assessment** (`carrier/submissions/[code]/loss/page.tsx`)
  - Scatter shows peers + subject, not subject alone (cohort fetch + render). Mostly Phase M.
- **Carrier Workbench Referral Actions** (`carrier/submissions/[code]/referral/page.tsx`)
  - Signal audit matrix populated. Mostly Phase M; render path must read it.

## COHORT L — Mobile refinements (README #4)
- Diff `frontend/src/components/mobile/{primitives,FeedSections,SignalHero,ReplySheet,MobileApp}.tsx` against `/tmp/dsi-3103/.../mobile/{widgets,app,feed_data}.{jsx,js}`. Apply spacing / hierarchy / interaction deltas only; data path remains `mobileFeed.ts`.

## COHORT M — Seed richness (single backend pass)
- Extend `seed/demo_reset.py` so every demo submission carries:
  - **≥3 historical model versions** (Q1/Q2/now), each with composite delta, so Risk Insights premium evolution and score history render.
  - **Populated `modifiers_applied`** chain on the latest MV: at least Base → Categorical → Signal → (Loss|Exposure) → Technical for the majority of coverages.
  - **`signal_evidence` rows** for the top contributory signals per coverage → Carrier Workbench Risk Assessment + Referral Actions audit matrix.
  - **`peer_cohort` scatter data** ≥10 anonymised peers per cohort → Loss + Exposure scatter renders.
  - **`commercial.carrier_name`** populated on every bound coverage → Broker Coverages carrier column.
- Verify by:
  - AST-parse + a fresh `python -m seed demo-reset --rng-seed 42` run (if env permits).
  - Field-checking the three demo client logins against the live `/portal/overview` / `/score` / `/peers` payloads.

## COHORT N — Dynamic vs placeholder transparency
- New tiny primitive `components/ui/data-origin.tsx` exporting `<DataOriginBadge level="signal|derived|seed|placeholder" />` and `<DataOriginLegend />`.
- Each page footer (or topbar slot) hosts an `i` button opening a popover listing every card/section with its origin token. Tokens map to colours: signal=info, derived=aux, seed=mute, placeholder=spot.
- One pass per persona; legends live alongside the page (so the page owns its provenance).

---

## File map (delta from F/G/H)
| Surface | New / changed |
|---|---|
| Chrome | `components/chrome/persona-sidebar.tsx` (hover-only, no shift), `workbench-shell.tsx` (sidebar normalisation), `topbar.tsx` (title de-dup helper if needed) |
| Client portal | `client/page.tsx`, `client/drivers/page.tsx`, `client/peers/page.tsx`, `client/scenarios/page.tsx`, `client/actions/page.tsx` (all switcher-wrapped), `client/coverages/page.tsx` (link rewrite), `client/coverages/[code]/page.tsx` (NEW), `client/profile/page.tsx` (soften), `client/request/page.tsx` (gating + config-sourced lines) |
| Broker portal | `broker/page.tsx` (layout J1), `broker/coverages/page.tsx` (carrier col), `broker/client-health/page.tsx`, `broker/market/page.tsx` |
| Carrier workbench | `carrier/submissions/[code]/{summary,pricing,risk,loss,referral}/page.tsx` + shell scroll fix |
| Shared | `components/portal/CoverageSwitcher.tsx` (NEW), `components/portal/PageHead.tsx` (NEW), `components/ui/data-origin.tsx` (NEW) |
| Backend | `routes/portal/schemas.py`, `routes/portal/overview.py`, `routes/portal/broker_intel.py` (carrier col), `seed/demo_reset.py` (Phase M reseed) |

## Acceptance criteria
- All four demo logins (`client.acme`, `client.northwind`, `client.pioneer`, `marsh.admin`, `demo.underwriter`) load every persona page without 500s.
- No remaining "looks-placeholder" complaints once Phase M is run.
- Sidebar visually identical in motion across all surfaces; no scrollbar in workbench sidebar.
- Coverage switcher consistent across 5 pages; deep links work.
- Broker Coverages shows a real carrier name for every bound coverage post-reseed.
