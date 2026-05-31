# V10 Phase 7 — Broker Portal: Evidence-Aware Book & Client Workbench

**Status:** Planning
**Depends on:** Phase 1 (projection w/ `detail=broker`), Phase 5 (broker disclosure), Phase 6 (client-side patterns to mirror)
**Audience:** broker
**Backend precondition:** Phase 1 `?detail=broker` superset + Phase 5 `/portal/submissions/{code}/disclosure`.

The broker sits between client and carrier. They need to know, across their whole book and per client, **which findings are solid and which are soft** — so they know what to relay, what to contest, and where to coach. This phase makes the broker portal evidence-aware.

---

## A. What has been built (backend)
- Phase 1 broker superset: `GET /portal/submissions/{code}/evidence?detail=broker` (curated + provenance summary + `has_provenance`; still no validator internals).
- Phase 5 broker disclosure: `GET /portal/submissions/{code}/disclosure`.
- Already-wired broker data (`lib/portalApi.ts`): `/portal/overview` (book), `/client-health`, `/clients/{entity}` (workbench), `/placement/{code}`, `/book-health`, `/aggregation`, `/communications`, `/queries`.

## A.1 Existing broker surfaces to enhance (verified)
```
frontend/src/app/(app)/broker/
  page.tsx        Book of clients
  client-health/  engagement + flags
  clients/        per-client workbench (covs, loss, threads, score, premium, exposure, terms, opportunities)
  coverages/      cross-client coverage view
  placement/      carrier matching
  communications/ query threads
  book-health/    portfolio analytics
  aggregation/    CAT + concentration
```

---

## B. What it augments & why
Augments the broker **book table** (`broker/page.tsx`), the **client workbench** (`broker/clients/...`), and **book-health**. Today the broker sees scores, tiers, premiums, percentiles — but not evidential strength. Two clients at tier 3 are not equivalent if one is built on attested evidence and the other on inferred guesses; the latter is fragile (a re-pull could move it) and is exactly where a broker adds value by supplying real data. Evidence grades turn the book into a **prioritised action list**: chase the soft-but-material findings.

Why per surface: **book table** — a book-wide "evidence health" column flags fragile assessments; **client workbench** — per-signal grades tell the broker what to attest on the client's behalf; **book-health** — an evidence-quality distribution across the portfolio.

---

## C. Frontend implementation (broker)

### C.1 API + types
`lib/portalApi.ts`: `fetchSubmissionEvidence(code, {detail:"broker"})`, `fetchSubmissionDisclosure(code)`. Extend the book/workbench view-models in `types/portal.ts` with an evidence summary per client/coverage.

### C.2 Surface-by-surface
- **`broker/page.tsx` (book)**: add an **"Evidence health"** column — a compact `<EvidenceMeter>` (composite distribution) + min-grade badge per client row. Sort by "weakest evidence" to surface fragile assessments. A "soft-but-material" flag where a high-weight signal has a low grade.
- **`broker/clients/...` (workbench)**: in the coverage/score views, add the **`<EvidenceGradeBadge audience="broker">`** (short+tooltip) + basis per signal, plus the broker-superset **provenance summary** (`has_provenance`, source kinds) so the broker knows what's verifiable. Add a "what to attest" rail: low-grade, high-impact signals with the projected grade lift (mirrors client `actions`, broker framing).
- **`broker/communications` / workbench comms**: a "Disclosure packet" action (Phase 5) for the active submission, to forward/explain a carrier decision; and a "request evidence from client" affordance tied to `absence_failed_fetch` signals.
- **`broker/book-health`**: an **evidence-quality distribution** chart (`charts/` — reuse `cohort-bar`/`bell-curve` idioms) across the portfolio: % of book by min-grade band; a "fragility index" (share of material findings below `corroborated`).

### C.3 Excluded for broker
Validator axes, calibration, mechanism memory, commitment internals, raw cluster ids — carrier-only (Phase 3/4). Broker gets grades, basis, provenance summary, and the full own-client disclosure packet (Phase 5).

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| per-signal grade + basis | ✅ | ✅ (+provenance summary) | ✅ (+full sources) |
| book/portfolio evidence rollup | n/a | ✅ | ✅ (analytics) |
| disclosure packet | ❌ | ✅ (own client) | ✅ |
| validator/calibration/mechanism | ❌ | ❌ | ✅ |

---

## D. States
- Book client with no evidence yet: neutral "—" in the evidence column (not zero).
- Workbench signal absent: `<AbsenceTag>`; `absence_failed_fetch` highlighted as "attest opportunity".

## E. Definition of done
- Broker book table shows an evidence-health column, sortable by weakest evidence.
- Client workbench shows per-signal grades + provenance summary + "what to attest" rail.
- Book-health shows the evidence-quality distribution / fragility index.
- Broker can open an own-client disclosure packet; cross-client 404s.
