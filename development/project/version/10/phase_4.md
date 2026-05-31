# V10 Phase 4 — Carrier Ops: Mechanism Memory · Delta Events · Recompute

**Status:** Planning
**Depends on:** Phase 1, Phase 2
**Audience:** carrier only
**Backend precondition:** none (all endpoints live)

The "living submission" capabilities: recall of similar historical risk patterns, a feed of what external events triggered re-extraction, and a manual recompute trigger. These make the workbench reflect a risk that changes after binding.

---

## A. What has been built (backend)

### A.1 Mechanism memory + recall (live, `assessment:read`)
`infrastructure/api/routes/mechanism.py`:
```
GET /api/v1/mechanisms?primitive_type&coverage&limit                      -> MechanismDTO[]
GET /api/v1/model-versions/{mv}/signals/{sig}/mechanisms                   -> MechanismDTO[]   (top-K recall: chromadb→tfidf→keyword)
```
`MechanismDTO`: `{ id, summary, primitive_type, sector_tags[], tags[], what_made_it_high_grade, recall_count }`.

### A.2 Delta events + recompute (live)
`infrastructure/api/routes/events.py` (HMAC, inbound feeds): `POST /events/external/{sec_edgar|companies_house|ofac}`.
`infrastructure/api/routes/recompute.py` (auth `assessment:refer`):
```
POST /api/v1/recompute  body { submission_id, entity_id, signal_ids?, primitive_types?, note? } -> { queued }   (202)
```
`infrastructure/api/routes/entity_events.py` (auth `assessment:read`):
```
GET /api/v1/submissions/{sub}/entity-events?limit -> EntityEventDTO[]
```
`EntityEventDTO`: `{ id, event_type, source_feed, received_at, dispatched_at, blast_radius[], resulting_model_version_id, payload{} }`.

---

## B. What it augments & why
Augments the carrier workbench. The entity-event feed is a natural fit for the existing **`versions`** tab (`carrier/submissions/[code]/versions`) — entity events are precisely what produce new model versions, so the feed and the lineage belong together (add an "External updates" section, or a sibling `events` tab if cleaner). Mechanism recall enriches the Phase 2 evidence drawer.

Why the carrier needs each: **mechanism recall** — "we've seen this pattern before, here's what made it high-grade evidence" accelerates and grounds judgement; **entity-events** — an audit trail of *why* a model version was superseded (which feed fired, what blast radius); **manual recompute** — when an underwriter knows something changed, re-pull the affected signals without re-running everything.

---

## C. Frontend implementation (carrier)

### C.1 API + store
Extend `store/dsiStore.ts` / `lib/api.ts`: `fetchMechanisms(filters)`, `fetchSignalMechanisms(mvId, sigId)`, `fetchEntityEvents(subId)`, `postRecompute(body)`.

### C.2 Mechanism recall (in the Phase 2 evidence drawer)
- **`<MechanismRecall mvId signalId />`** — a "Seen before" section: top-K `MechanismDTO` cards (`ui/card`) showing `summary`, `what_made_it_high_grade`, `sector_tags`, `recall_count`. Optional global browser at `/carrier/mechanisms` (`admin-table` over `/mechanisms` with primitive/coverage filters).

### C.3 Entity-event feed (into the `versions` tab)
- **`<EntityEventFeed subId />`** — a timeline (reuse the version-history idiom): each event = `source_feed` icon, `event_type`, `received_at`→`dispatched_at`, `blast_radius` chips (signal ids re-extracted), and a link to `resulting_model_version_id` (the new MV it produced). Pending events (`dispatched_at===null`) shown as "queued".

### C.4 Manual recompute
- **`<RecomputeButton subId entityId />`** — carrier action (gated `assessment:refer`); opens a small form (choose `signal_ids` and/or `primitive_types`, optional `note`), POSTs `/recompute`, shows the 202 "queued" toast (`shared/NotificationToast`), and refreshes the entity-event feed.

### C.5 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| anything in this phase | ❌ | ❌ | ✅ |

---

## D. States
- No mechanisms recalled: "No comparable patterns on file."
- No entity events: "No external updates since assessment."
- Recompute queued: optimistic "queued" event node; poll the feed for `dispatched_at` + `resulting_model_version_id`.

## E. Definition of done
- Evidence drawer shows mechanism recall for a signal.
- `versions` tab shows the entity-event feed with blast-radius chips and MV links.
- `<RecomputeButton>` POSTs `/recompute` and the new event appears in the feed.
- No client/broker surface touched.
