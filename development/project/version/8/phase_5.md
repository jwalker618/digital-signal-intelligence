# Version 8 Phase 5: Broker Query/Reply on Referrals

## Overview

Extend the existing referral state machine with a **message thread** between underwriters and brokers, plus a new state `AWAITING_BROKER`. When an underwriter raises a query, the referral pauses and waits. When the broker replies (with a signal-affecting value change), the system **automatically re-assesses** the submission and updates the quote.

This is the closed-loop interaction at the heart of the demo: Act 4 (carrier raises query) → Act 5 (Marsh replies) → Act 6 (re-assessment improves score, premium drops).

## Rationale

v7 has a referral state machine — `PENDING`, `IN_REVIEW`, `APPROVED`, `DECLINED`, `MODIFIED` — but no concept of "we're waiting on the broker." Underwriters today have no way to ask the broker a question and have the system pick up the answer automatically. Without this, the demo's flow has nowhere to land Marsh's reply.

The implementation reuses the existing workflow for re-assessment. Phase 5 adds no new pricing or scoring logic — it adds a communication channel and an event trigger.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| New referral state | `AWAITING_BROKER` added to existing enum | Single state addition; existing flow unchanged |
| Message model | New `ReferralMessage` table, FK to `Referral` | Keeps thread separate from referral row |
| Who can raise a query | Users with `assessment:refer` (underwriters) | Reuses existing permission |
| Who can reply | Users with `portal:broker:reply` (Phase 1) | Broker-only reply path |
| Reply triggers re-assessment | Yes — if reply carries a `signal_value_update` payload | Without an update, just a comment exchange |
| Re-assessment path | Re-invoke existing `layers/risk/workflow.py` with the updated signal value applied via direct query override (mechanism already exists) | No new pricing path |
| State transitions | `PENDING/IN_REVIEW → AWAITING_BROKER` (on query raise); `AWAITING_BROKER → IN_REVIEW` (on broker reply) | One new state, two transitions |
| Notifications | UI inbox only (`/portal/queries`); no email/webhook in v8 | Out of scope: notifications are v8.1 |
| Multiple queries on one referral | Allowed — they appear as separate message thread entries | Underwriter can raise multiple queries; broker replies to whichever |

## Current State

- `infrastructure/api/routes/referrals.py` — referral CRUD and state transitions.
- `infrastructure/db/models.py` — `Referral` model (per recon), state enum (`PENDING`, `IN_REVIEW`, `APPROVED`, `DECLINED`, `MODIFIED`).
- `layers/risk/workflow.py` — assessment workflow, supports direct query overrides (per recon, signal absences/queries are part of the existing referral mechanism).
- No `ReferralMessage` or equivalent thread model. No `AWAITING_BROKER` state.

## Target State

### Data model additions

```python
# infrastructure/db/models.py

class ReferralState(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    AWAITING_BROKER = "AWAITING_BROKER"   # NEW
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    MODIFIED = "MODIFIED"

class MessageDirection(str, Enum):
    UNDERWRITER_TO_BROKER = "U2B"
    BROKER_TO_UNDERWRITER = "B2U"

class ReferralMessage(Base):
    __tablename__ = "referral_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey("referrals.id"), nullable=False, index=True)
    direction: Mapped[MessageDirection] = mapped_column(nullable=False)
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    signal_value_update: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # ^ optional payload: {"signal_id": "mfa_enabled", "new_value": true, "evidence_url": "..."}
    triggered_reassessment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    new_quote_id: Mapped[int | None] = mapped_column(ForeignKey("quotes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, index=True)

    referral: Mapped["Referral"] = relationship(back_populates="messages")

class Referral(Base):
    # ... existing fields ...
    awaiting_party: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # "broker" when awaiting broker reply; null otherwise. Redundant with state but allows easy queue queries.
    messages: Mapped[list["ReferralMessage"]] = relationship(
        back_populates="referral", order_by="ReferralMessage.created_at"
    )
```

### Migration

Alembic migration `latest + 3` (after Phase 1's `+1` and Phase 2's `+2`):

1. Add `AWAITING_BROKER` to the referral state enum.
2. Add `awaiting_party` column to `referrals` (nullable string).
3. Create `referral_messages` table with the schema above.

Down migration reverses.

### Endpoints

Two new endpoints, mounted at `/api/v1/referrals/{referral_id}/messages`. Implementation in `infrastructure/api/routes/referral_messages.py`. **Mounted in `infrastructure/api/main.py` in this phase.** Phase 6 will mount the portal-scoped versions of these endpoints separately.

#### `POST /api/v1/referrals/{referral_id}/messages` — raise query (underwriter side)

**Permissions**: `assessment:refer`.

**Request:**
```json
{
  "body": "Please confirm MFA status across admin accounts.",
  "request_signal_evidence": "mfa_enabled"
}
```

`request_signal_evidence` is optional; when present, it hints to the broker UI which signal the underwriter wants evidence for.

**Behaviour:**
- Append `ReferralMessage` with `direction=U2B`, `body`, `signal_value_update=None`.
- Transition referral state to `AWAITING_BROKER`. Set `awaiting_party="broker"`.
- If referral was `APPROVED` or `DECLINED`, reject with 409 — terminal states cannot be re-queried.

**Response:**
```json
{
  "message_id": 42,
  "referral_state": "AWAITING_BROKER",
  "referral_id": 17
}
```

#### `POST /api/v1/referrals/{referral_id}/messages/reply` — reply (broker side)

**Permissions**: `portal:broker:reply`.

Additionally, the requesting user's `broker_id` must match the broker associated with the referred entity. If mismatched, reject with 403.

**Request:**
```json
{
  "body": "MFA was deployed across all admin accounts in Q1 2026. See attached attestation.",
  "signal_value_update": {
    "signal_id": "mfa_enabled",
    "new_value": true,
    "evidence_basis": "Internal attestation, Q1 2026 IT ops report"
  }
}
```

`signal_value_update` is optional. When present, it carries a direct query response that will be applied as a signal override and trigger re-assessment.

**Behaviour:**
1. Append `ReferralMessage` with `direction=B2U`, `body`, `signal_value_update`.
2. If referral is not `AWAITING_BROKER`, the reply is still accepted (broker can comment without a pending query) but **no re-assessment triggers**.
3. If `signal_value_update` is None: no re-assessment, set referral state to `IN_REVIEW`, clear `awaiting_party`.
4. If `signal_value_update` is present:
   - Apply the update as a direct-query signal override on the entity.
   - Invoke `layers/risk/workflow.py` to re-assess.
   - On a new `Quote` produced, link `ReferralMessage.new_quote_id = new_quote.id` and set `triggered_reassessment = True`.
   - Update the referral row: state → `IN_REVIEW` (the new quote may itself raise new referrals, but the original referral re-enters IN_REVIEW for underwriter review). Clear `awaiting_party`.

**Response:**
```json
{
  "message_id": 43,
  "triggered_reassessment": true,
  "new_quote_id": 88,
  "referral_state": "IN_REVIEW"
}
```

#### `GET /api/v1/referrals/{referral_id}/messages` — list thread

**Permissions**: `assessment:refer` OR (`portal:broker:reply` AND broker matches referral's entity).

Returns all messages in chronological order, including signal updates and re-assessment links.

### Re-assessment mechanics

Direct query override application: the existing workflow (per recon) supports direct-query response paths. Phase 5's re-assessment path:

```python
def reassess_with_signal_override(session, entity_id: int, coverage_line: str,
                                  signal_id: str, new_value: Any, evidence_basis: str) -> Quote:
    """
    Apply a direct-query signal override and re-invoke the full workflow.
    """
    # 1. Persist the signal override as a direct-query response (existing mechanism)
    # 2. Re-invoke run_assessment(entity, coverage_line) — same workflow as initial submission
    # 3. Return the new Quote (which will have its own cohort percentile, impact breakdown, etc. via Phases 2 & 3)
```

Implementation location: `layers/risk/reassessment.py` (new) or extend an existing helper if one exists in `layers/risk/`.

**Critical**: re-assessment uses the **same workflow** that produced the original quote. No new pricing path. If a signal_id is unknown, raise `UnknownSignalError` (HTTP 400 at the API layer).

### State machine reference

```
PENDING --(underwriter starts review)--> IN_REVIEW
IN_REVIEW --(underwriter raises query)--> AWAITING_BROKER
AWAITING_BROKER --(broker replies)--> IN_REVIEW
IN_REVIEW --(underwriter approves)--> APPROVED  [terminal]
IN_REVIEW --(underwriter declines)--> DECLINED  [terminal]
IN_REVIEW --(underwriter modifies + approves)--> MODIFIED  [terminal]

AWAITING_BROKER --(underwriter overrides reply, e.g. broker non-responsive)--> IN_REVIEW
```

The last transition (underwriter override) exists so a stalled query doesn't lock the referral forever. Implemented via a state-change endpoint on the referral (likely already exists; verify in discovery).

### Wiring in main.py

```python
# infrastructure/api/main.py
from infrastructure.api.routes import referral_messages
app.include_router(referral_messages.router, prefix="/api/v1")
```

Single touch. Phase 6 will mount the portal router separately.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Exact `Referral` model location and field names.
2. Exact `ReferralState` enum location and how it's stored (DB enum, string column).
3. The existing referral state-change endpoint (for the override transition).
4. The existing signal override / direct-query response mechanism in the workflow.
5. Whether `Quote` has a `referral_id` back-reference, and how re-assessment relates to the original referral row.

### Step 2: Migration

Write and test `latest + 3` migration: add state enum value, add `awaiting_party` column, create `referral_messages` table. Apply + rollback locally.

### Step 3: Models

Add `MessageDirection` enum and `ReferralMessage` model. Add `awaiting_party` and `messages` to `Referral`.

### Step 4: Re-assessment helper

Implement `layers/risk/reassessment.py` (or appropriate location): `reassess_with_signal_override(...)`. Heavy reuse of existing workflow — Phase 5's job is wiring, not new logic.

### Step 5: Endpoints

Implement `infrastructure/api/routes/referral_messages.py`:
- `POST .../messages` (raise query)
- `POST .../messages/reply` (broker reply, with optional re-assessment trigger)
- `GET .../messages` (list thread)
- Pydantic request/response models.
- Permission decorators.

### Step 6: Mount in main.py

Add the router include in `infrastructure/api/main.py`. Single line.

### Step 7: Tests

`tests/api/test_referral_messages.py`:

- Underwriter raises query: referral transitions to `AWAITING_BROKER`, `awaiting_party="broker"`, message appears in thread.
- Underwriter cannot raise query on terminal referral (`APPROVED`/`DECLINED`): 409.
- Broker (matching broker_id) replies without signal update: state → `IN_REVIEW`, no new quote, no `triggered_reassessment`.
- Broker replies with signal update: state → `IN_REVIEW`, new quote created, `new_quote_id` populated, `triggered_reassessment=True`. Assert new quote's `composite_score` differs (or equals if signal didn't move score — both are valid outcomes).
- Broker with mismatched broker_id: 403.
- User without `portal:broker:reply`: 403.
- User without `assessment:refer` raising query: 403.
- List thread returns messages in chronological order.
- Underwriter can override stalled `AWAITING_BROKER` back to `IN_REVIEW` (existing state-change endpoint).

`tests/risk/test_reassessment.py`:

- Direct call to `reassess_with_signal_override` produces a new Quote.
- Signal override is correctly applied — the new quote's modifiers reflect the new signal value.

### Step 8: Integration sanity test

`tests/integration/test_query_loop.py`:

1. Create entity with broker assigned, score it, generate a quote in REFER tier.
2. Underwriter raises query.
3. Broker replies with signal_value_update that materially improves the signal.
4. Assert new quote has higher score, lower premium, and the referral_state is `IN_REVIEW`.

This is the demo-Act-4-to-Act-6 path in test form. If this passes, the demo can flow.

## Constraints & Principles

1. **No new pricing or scoring logic.** Re-assessment invokes the existing workflow.
2. **State machine is sacred.** Only the documented transitions are allowed. No state shortcuts. Tests enforce.
3. **Permissions enforced at endpoint level.** Broker reply requires both the role permission AND broker_id match.
4. **Idempotent message creation.** Same payload posted twice creates two messages (intentional — repeat queries are valid). No deduplication.
5. **Re-assessment is synchronous.** v8 does not introduce async/queue infrastructure for re-assessments. Acceptable because typical re-assessment is <1s.
6. **No notifications.** UI inbox only. No emails, no webhooks, no WebSocket events. v8.1 may add.
7. **Audit trail intact.** Every message records author, direction, timestamp. Re-assessment links via `new_quote_id`.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Direct query override mechanism doesn't exist as recon assumes | Step 1 discovery confirms; if absent, this becomes a sub-phase. Per recon's referral state machine (`PENDING/IN_REVIEW/APPROVED/DECLINED/MODIFIED`), the path exists. |
| Re-assessment slow on large entities | Use existing workflow; if it's slow today, it's slow here. Out of scope to optimise in Phase 5. |
| Broker can spam replies | Endpoint accepts any reply; rate-limiting is v8.1. |
| Underwriter raises query on referral that was already moved to terminal state by race | 409 with state info; client handles. |
| Signal_id in reply is unknown to the coverage | 400 with error; broker UI validates against allowed signals. |
| Multiple queries open at once (state can only be AWAITING_BROKER once) | One referral, one open query at a time — state tracks. Multiple parallel queries would require redesign; v8 single-thread per referral. |
| New quote raises ANOTHER referral and the loop confuses users | Each new quote can spawn its own referral. The original referral row's state becomes IN_REVIEW; the new quote may or may not have its own referral row. UI must surface "linked quotes" — addressed in Phase 8. |

## Dependencies

- **Phase 1 complete.** `Broker`, broker_id FK, `BROKER` role, `portal:broker:reply` permission all exist.
- **Phase 3 recommended** — newly produced quotes from re-assessment will have impact_breakdown populated; without Phase 3 the new quote is still valid but lacks the field.
- **Phase 2 recommended** — same logic for cohort percentile on new quote.

## Success Criteria

1. Migration `latest + 3` adds `AWAITING_BROKER` state, `awaiting_party` column, `referral_messages` table.
2. `ReferralMessage` model and `MessageDirection` enum present.
3. Three endpoints live: POST messages, POST reply, GET thread.
4. Underwriter query → `AWAITING_BROKER` state.
5. Broker reply with signal_update → new quote created, state → `IN_REVIEW`.
6. Broker reply without signal_update → state → `IN_REVIEW`, no new quote.
7. Cross-broker reply attempts (broker_id mismatch) blocked.
8. All Step 7 tests pass.
9. Integration test (Step 8) demonstrates score-changing reply path end to end.
10. Router mounted in `main.py`.
11. Full `pytest tests/ -v` green.
12. No frontend, no seed, no other backend touches.

## Out of Scope (Phase 5)

- Portal-scoped endpoints (broker inbox view) — Phase 6.
- Frontend rendering of the message thread — Phase 8.
- Notifications (email/webhook/WebSocket) — v8.1.
- Multiple concurrent queries per referral — single thread per referral.
- Attachments on messages — body text only in v8.
- Message editing or deletion — append-only.
- Underwriter requesting evidence for multiple signals at once — one signal per query.
