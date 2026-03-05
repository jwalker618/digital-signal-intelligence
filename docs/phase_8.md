# Phase 8: Referral Workflow — DB Wiring & Missing APIs

## Overview

Phase 8 covers deterministic referral management: when the model returns `decision = refer`,
an underwriter reviews the flagged signals, optionally overrides them, and reaches a final
decision (approve / decline / modify). The data model and repository layer for this are fully
built. The problem is that **the API routes do not use them** — both `referrals.py` and
`quotes.py` run entirely on in-memory dicts with mock data.

This document describes every gap, why it matters, and exactly what needs to be implemented.

---

## Current State

### Routes vs. repositories

| Layer | File | State |
|---|---|---|
| DB models | `infrastructure/db/models.py` | Complete |
| Repositories | `infrastructure/db/repositories.py` | Complete |
| Referral routes | `infrastructure/api/routes/referrals.py` | In-memory mock only |
| Quote routes | `infrastructure/api/routes/quotes.py` | In-memory mock only |

Both route files declare module-level dicts at startup:

```python
# referrals.py line 43
_referrals: dict = {}

# referrals.py lines 334-335 (Phase 8 signal endpoints)
_signal_cache: Dict[str, Dict[str, Any]] = {}
_model_versions: Dict[str, Dict[str, Any]] = {}

# quotes.py line 34
_quotes: dict = {}
```

Every endpoint reads and writes these dicts. No repository is imported or called in either
file. Data does not survive a process restart and is invisible to any other worker.

---

## Work Required

### 1. Wire referral routes to `ReferralRepository`

**Affected endpoints:**
- `GET /referrals` — replace `_referrals` dict scan with `ReferralRepository.list_pending()`
- `GET /referrals/{referral_id}` — replace dict lookup with `ReferralRepository.get_by_id()`
- `PATCH /referrals/{referral_id}` — replace dict mutation with `ReferralRepository.review()`
- `GET /referrals/pending/count` — query DB instead of counting dict keys
- `GET /referrals/stats` — query DB instead of aggregating dict values

**Why:** Referrals created during submission processing (in `submissions.py`, which does use the
DB) will never appear in the referral list because the routes read a different data store. An
underwriter opening the queue sees only mock data seeded at startup.

**What `ReferralRepository` already provides:**
- `get_by_id(referral_id)` — by string ID
- `list_pending(assigned_to, limit)` — filtered by PENDING / IN_REVIEW status
- `assign(referral_id, assigned_to)` — sets assignee and transitions to IN_REVIEW
- `review(referral_id, reviewed_by, decision, notes, tier_override, premium_adjustment)` — sets
  final status, reviewer, and any manual adjustments

Each route needs a `db: AsyncSession = Depends(get_db)` parameter injected and a repository
instance constructed from it, following the pattern already used in `submissions.py`.

---

### 2. Wire quote routes to `QuoteRepository`

**Affected endpoints:**
- `GET /quotes` — replace `_quotes` dict scan with `QuoteRepository` query
- `GET /quotes/{quote_id}` — replace dict lookup with `QuoteRepository.get_by_id()`
- `POST /quotes/{quote_id}/bind` — replace dict mutation with `QuoteRepository.bind()`
- `POST /quotes/{quote_id}/decline` — replace dict mutation (see gap 4 below)

**Why:** Quotes are created by the submission workflow and written to the DB. The quote routes
read a separate in-memory dict so a broker fetching `GET /quotes/{quote_id}` after submission
completes will always get a 404 or a generated mock, never the real quote.

**What `QuoteRepository` already provides:**
- `get_by_id(quote_id)`
- `get_by_submission(submission_id)`
- `bind(quote_id, bound_by, policy_number)`
- `expire_old_quotes()`

---

### 3. Wire signal override routes to DB repositories

**Affected endpoints:**
- `GET /referrals/{referral_id}/signals` — must read from `SignalCacheRepository`
- `POST /referrals/{referral_id}/signals/override` — must write to `SignalCacheRepository`,
  `SignalAuditRepository`, and `ModelVersionRepository`
- `DELETE /referrals/{referral_id}/signals/{signal_id}/override` — must revert via the same
  three repositories
- `GET /referrals/{referral_id}/model-versions` — must read from `ModelVersionRepository`

**Current behaviour:** These endpoints use `_signal_cache` and `_model_versions` dicts
seeded with five hardcoded mock signals (`tls_configuration`, `security_headers`, etc.)
per referral. No actual signal data is read from the DB, and no audit records are written.

**What the DB layer already provides:**

`SignalCacheRepository`:
- `get_valid_cached(entity_id, signal_id, source_name)` — TTL-aware retrieval
- `get_entity_signals(entity_id)` — all cached signals for an entity
- `set(...)` — write or replace a cache entry
- `invalidate(entity_id, signal_id)` — purge on revert

`SignalAuditRepository`:
- `create_override(signal_cache_id, model_version_id, signal_id, entity_id, inferred_value,
  audited_value, overridden_by, rationale, evidence_reference, score_impact, tier_impact)` —
  creates the immutable audit record
- `get_by_model_version(model_version_id)` — audit trail for a version
- `get_latest_audited_value(entity_id, signal_id)` — current override state

`ModelVersionRepository`:
- `create(submission_id, version_type, **kwargs)` — auto-increments version_number, clears
  is_latest on previous version, returns new record
- `get_latest(submission_id)` — O(1) via partial index
- `list_for_submission(submission_id)` — full version history

**Required sequence for `POST /referrals/{referral_id}/signals/override`:**

```
1. Load referral → get quote_id → get quote → get submission_id and model_version_id
2. Load signal from SignalCacheRepository.get_valid_cached()
3. Preserve signal.inferred_value (must not be changed)
4. Set signal.audited_value = override.audited_value, signal.is_overridden = True
   via SignalCacheRepository.set() or direct update
5. Recalculate composite score and tier using all signals
   (audited_value where is_overridden=True, else inferred_value)
6. Create new ModelVersionRecord via ModelVersionRepository.create()
   with version_type="signal_override" and recalculated scoring fields
7. Create SignalAuditRecord via SignalAuditRepository.create_override()
   linked to the new model_version_id
8. Update quote.model_version_id to point to the new model version
   (see gap 4 — QuoteRepository.update_model_version_id() needs adding)
9. Return SignalOverrideResponse with score_impact, tier_impact, new model version IDs
```

**Why the audit record matters:** `signal_audit_records` is the permanent, immutable record
of what the machine inferred vs. what the underwriter judged. It is the evidentiary trail for
regulatory and claims purposes. Writing only to an in-memory dict means none of this is
persisted.

---

### 4. Add missing `QuoteRepository` methods

Two operations on quotes have no repository support:

#### `update_model_version_id(quote_id, model_version_id)`

Every signal override and every manual tier/premium adjustment creates a new
`ModelVersionRecord`. The quote's `model_version_id` FK must be updated to track the latest
version — otherwise `GET /quotes/{quote_id}` returns scoring data from v1 (the initial machine
run) even after an underwriter has materially changed the inputs.

```python
async def update_model_version_id(
    self,
    quote_id: str,
    model_version_id: uuid.UUID,
) -> Optional[Quote]:
    await self.db.execute(
        update(Quote)
        .where(Quote.quote_id == quote_id)
        .values(model_version_id=model_version_id, updated_at=datetime.utcnow())
    )
    return await self.get_by_id(quote_id)
```

#### `update_status(quote_id, status)`

When a referral is approved, the quote must flip from its intermediate state to `READY` so it
can be bound. When a referral is declined, the quote must become `DECLINED`. Currently neither
transition is persisted — `GET /referrals/{referral_id}/quote` computes the effective status
in memory at read time, so the quote record in the DB never changes.

```python
async def update_status(
    self,
    quote_id: str,
    status: QuoteStatus,
) -> Optional[Quote]:
    await self.db.execute(
        update(Quote)
        .where(Quote.quote_id == quote_id)
        .values(status=status, updated_at=datetime.utcnow())
    )
    return await self.get_by_id(quote_id)
```

---

### 5. Add `POST /referrals/{referral_id}/assign` endpoint

`ReferralRepository.assign()` exists and is correct. There is no route that calls it.

An underwriter needs to be able to claim a referral before reviewing it — this is what
transitions the status from `PENDING` to `IN_REVIEW` and records who is responsible. Without
it, referrals can only be in `PENDING` status; the `IN_REVIEW` state is unreachable via the
API.

**Endpoint to add:**

```
POST /referrals/{referral_id}/assign
Body: { "underwriter_id": "<uuid>" }
Response: ReferralDetail
```

Calls `ReferralRepository.assign(referral_id, assigned_to=underwriter_id)`. Returns the
updated referral. Should 409 if already assigned to someone else; 400 if already resolved.

---

### 6. Create a new `ModelVersionRecord` on manual tier/premium adjustment

When `PATCH /referrals/{referral_id}` is called with `tier_override` or `premium_adjustment`
in the adjustments payload, those values are stored on the `Referral` row. A new
`ModelVersionRecord` is not created.

**Why this is wrong:** The design principle established in Phase 8 is that every material
change to the risk picture produces a new versioned model output. A manual tier override is at
least as significant as a signal override — it directly determines the price offered to the
insured. Without a new model version, there is no way to know from the `model_versions` table
alone what the final agreed tier and premium were; you would have to cross-reference the
`referrals` table.

**Required sequence inside `PATCH /referrals/{referral_id}` when adjustments are present:**

```
1. Call ReferralRepository.review() to persist decision and adjustments on referral row
2. If tier_override or premium_adjustment is set:
   a. Load current latest ModelVersionRecord for the submission
   b. Create new ModelVersionRecord via ModelVersionRepository.create()
      with version_type="referral_adjustment"
      copying all fields from current latest, then applying tier_override / recalculated premium
   c. Call QuoteRepository.update_model_version_id() to point quote at new version
3. Call QuoteRepository.update_status():
   - APPROVE / MODIFY → QuoteStatus.READY
   - DECLINE → QuoteStatus.DECLINED
4. Write AuditLog entry
```

---

## Referral Lifecycle — Complete DB Write Sequence

For reference, the complete set of DB writes that should occur across a referred submission:

| Event | Tables written |
|---|---|
| Submission created | `submissions` |
| Workflow runs, decision = refer | `model_versions` (v1, is_latest=true), `quotes` (status=READY initially, then REFERRED), `referrals` (status=PENDING) |
| Underwriter assigns referral | `referrals` (assigned_to, assigned_at, status=IN_REVIEW) |
| Underwriter overrides a signal | `signal_cache` (audited_value, is_overridden=true), `signal_audit_records` (new row), `model_versions` (new row v2+, is_latest=true; v1 is_latest=false), `quotes` (model_version_id updated) |
| Underwriter reverts a signal override | `signal_cache` (audited_value=null, is_overridden=false), `signal_audit_records` (new row), `model_versions` (new row), `quotes` (model_version_id updated) |
| Underwriter approves (no adjustment) | `referrals` (reviewed_by, reviewed_at, review_decision, status=APPROVED), `quotes` (status=READY) |
| Underwriter approves with adjustment | All of the above + `model_versions` (new row, version_type=referral_adjustment), `quotes` (model_version_id updated, status=READY) |
| Underwriter declines | `referrals` (status=DECLINED), `quotes` (status=DECLINED) |
| Broker binds quote | `quotes` (status=BOUND, bound_at, bound_by, policy_number) |

All DB writes should have a corresponding `audit_logs` entry.

---

## Files to Change

| File | Changes |
|---|---|
| `infrastructure/api/routes/referrals.py` | Replace all `_referrals`, `_signal_cache`, `_model_versions` dict usage with repository calls; inject `db` session; add assign endpoint |
| `infrastructure/api/routes/quotes.py` | Replace all `_quotes` dict usage with repository calls; inject `db` session |
| `infrastructure/db/repositories.py` | Add `QuoteRepository.update_model_version_id()` and `QuoteRepository.update_status()` |

No schema changes are required. No new migrations are needed. The existing models and
repositories support the full workflow as described.
