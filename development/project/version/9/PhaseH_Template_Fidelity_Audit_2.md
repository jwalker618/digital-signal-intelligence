# Version 9 — Phase H: Second Template-Fidelity Audit

**Status:** Core fixes SHIPPED — remaining items triaged below
**Branch:** `claude/nice-ride-xSz7t`
**Source of truth:** `/tmp/dsi-revised/client_review/*.jsx` + `chrome.css`
(from `Digital Signal Intelligence - Revised.zip`)

## Trigger
User found live discrepancies vs the templates after using the desktop UX:
1. Top-right org badge ("Marsh") showing in broker/client/carrier portals.
2. Sidebar still had the DSI symbol/wordmark at the top.
3. Book roster missing its quick filters.
A fresh 3-agent parallel audit (chrome+client / broker / carrier+admin) was run.

---

## ✅ SHIPPED

### Chrome (affects every page)
- **Topbar org badge** now renders ONLY on `/admin` routes. Template
  (`primitives.jsx` FrameReimag) gates it on `persona === 'admin'` — "the
  badge would just echo the user's own org, which they already know."
  → `components/chrome/topbar.tsx` (pathname-gated `showEntity`).
- **Sidebar collapsed rail**: removed the DSI wordmark logo; added the thin
  rule divider after the toggle (`24×1px`, matches `.sb-rule`); added a
  log-out button pinned to the bottom. Rail narrowed `72px → 60px` (template
  `min-width: 60px`).
- **Sidebar expanded overlay**: removed the "DSI" wordmark/text header;
  added the account block (avatar initials + name + email, matches
  `.sbx-account`); footer is now **Settings + Log out** (was a single
  Profile link, matches `.sbx-foot`).
  → `components/chrome/persona-sidebar.tsx`.
- **Shared identity helper** extracted: `lib/userIdentity.ts`
  (`deriveUserDisplay`) — now used by both the profile page and the sidebar
  account block (DRY; removed the duplicate `deriveDisplay` in profile).

### Broker · Book of Clients (`broker/page.tsx`)
- **Vertical quick-filter chips** added to the roster header ("Filter: All
  · …"), data-driven from each policy's practice vertical. Backed by a new
  `vertical` / `vertical_name` field on `ClientBookEntry`, derived server-side
  from the submission NAICS via `vertical_for_naics` (no extra query).
  → `schemas.py`, `overview.py` (`_build_book_entry`), `types/portal.ts`,
    `broker/page.tsx` (new `VFilterChip`, filter state, empty-state copy).

### Carrier · Pipeline (`carrier/page.tsx`)
- **Line quick-filter chips** added (data-driven from the coverage lines
  present), plus the **"Sort: oldest first"** caption. The queue is now
  actually sorted oldest-first so the caption is truthful.

### Client · Coverages (`client/coverages/page.tsx`)
- Lines now sorted by total premium **descending**; label corrected to
  **"Sort: by premium ↓"** (template `reim_coverages.jsx:66`).

---

## ⏸ DEFERRED — honesty-rule (no data source)
- **Carrier column in the book roster / broker coverages rows.** The
  template shows a carrier per policy, but there is **no carrier FK** on
  `Submission` or `Quote` in the DB (the carrier roster is reference data,
  not a per-policy binding). Adding the column would render a full column of
  "—". Per the standing honesty rule (Phase F "ACCEPT AS-IS"), left out
  until a real bound-carrier source lands. Broker coverages rows keep
  `submission_code` as the honest secondary label.
- **"Awaiting you" KPI subtext "of N open queries".** The backend returns
  only the awaiting-broker count, not the total-open denominator. Not
  fabricating a denominator; subtext stays "open queries".

---

## ⏸ DEFERRED — low-value / higher-risk (reviewed, intentionally not changed)
- **Topbar breadcrumb trail vs single segment.** Template's FrameReimag
  renders only the active page name; our drill-down pages append a 3rd crumb
  (coverage / referral code) as useful context. The trail is a sensible
  enhancement the user did NOT flag — kept. (Portal root crumb is already
  stripped.)
- **World Engine tables → CSS grid.** Same call as Phase F: the `<table>`
  renders correctly; a full grid rewrite carries more regression risk than
  the cosmetic gain.
- **Pixel nits** (coverages PolicyRow `0.8fr/1fr` vs `0.9fr/0.9fr`; comms
  chevron column `20px` vs `32px`): cosmetic, sub-pixel at desktop widths.
- **Book-health "Profitability" secondary metric** (template shows
  best-yielding line; impl shows avg premium/client): needs a per-line
  commission yield the endpoint doesn't aggregate yet.

---

## Verified clean (audit found no actionable drift)
Client overview/scenarios/request/comms/profile; broker
client-health/coverages/placement/carriers/recs/market/aggregation; carrier
workbench shell; all four admin pages. Component-abstraction and
`dark:`/responsive differences are intentional and not regressions.
