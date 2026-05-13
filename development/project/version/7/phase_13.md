# V7 Phase 13: Delta-Aware Re-Extraction

## Depends on
- Phase 5 (`signal_history`).
- Phase 9 (`primitive_type` for blast-radius routing).
- Phase 10 (cluster fact_class for trigger classification).

## Blocks
- Phase 14 (workbench surfaces "what changed since last cycle").

## Scope

Today every model cycle re-extracts every signal in the registry. That's wasteful and hides *what changed* in the audit trail. Lifted from Clearwing's `commit_monitor.py:1-40` blast-radius pattern: external **entity events** (new filing, new directorship, sanctions update, calibration-decision disagreement) trigger a focused re-extraction of only the *affected signals*.

Three event sources land in this phase:

1. **Webhooks** from external feeds (SEC EDGAR new-filing, Companies House change, OFAC update). Phase 13 implements the receiver + dispatcher; per-feed adapters are stubbed and filled by adopters.
2. **Internal**: a Phase 7 calibration decision where `human_grade != extractor_grade` triggers a targeted re-extraction of the disputed signal_id.
3. **Manual**: API endpoint `POST /api/v1/recompute` accepts `{submission_id, signal_ids?, primitive_types?}` and runs the targeted recompute.

Each event yields a **blast radius** — the set of signals whose value plausibly depends on the event. Computed from a static `signal_dependency_graph` (Phase 13 adds this; future phases keep it current).

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Event types | `entity_filing`, `entity_directorship`, `sanctions_update`, `human_calibration_disagreement`, `manual_recompute` |
| D2 | Blast radius | Static dependency graph in `infrastructure/recompute/signal_deps.py` — declarative: `{signal_id: {triggers: list[event_type], depends_on: list[signal_id]}}`. Authors maintain it; CI lint asserts every signal_id in registry has an entry |
| D3 | Receiver | One FastAPI router `/api/v1/events/external`. HMAC-verified per-feed. Per-feed adapter maps payload → internal `EntityEvent` |
| D4 | Storage | `entity_events` table — append-only, one row per received event. Indexed on `(entity_id, received_at)` and `(event_type, received_at)` |
| D5 | Targeted recompute | Wraps the existing cycle workflow with a `signal_filter` parameter. The workflow already supports running a subset; we make sure that's true and add the filter |
| D6 | Result | A new `ModelVersion` is created with `version_type=delta_recompute` and the unchanged signals are *copied* from the previous version (cheap; respects history) |
| D7 | Composite re-rollup | Always. After targeted re-extraction, composite grade rollup is recomputed across ALL signals (changed + copied) so the composite trail stays coherent |
| D8 | Audit | Each event + each delta recompute logged to `compliance_audit_logs` with `event_type` in `{entity_event_received, delta_recompute_started, delta_recompute_completed}` |
| D9 | Rate limiting | Max 1 delta recompute per (submission_id, signal_id) per hour. Subsequent triggers within the window queue into a single batched recompute |
| D10 | Auth | Webhooks: HMAC + IP allowlist per-feed. Manual API: existing JWT auth |

## Files

### Create
- `alembic/versions/028_entity_events.py`
- `infrastructure/recompute/__init__.py`
- `infrastructure/recompute/signal_deps.py`
- `infrastructure/recompute/blast_radius.py`
- `infrastructure/recompute/dispatcher.py`
- `infrastructure/recompute/adapters/__init__.py`
- `infrastructure/recompute/adapters/sec_edgar.py` (stub)
- `infrastructure/recompute/adapters/companies_house.py` (stub)
- `infrastructure/recompute/adapters/ofac.py` (stub)
- `infrastructure/api/routes/events.py`
- `infrastructure/api/routes/recompute.py`
- `tests/unit/test_blast_radius.py`
- `tests/unit/test_signal_deps_lint.py`
- `tests/api/test_events_webhook.py`
- `tests/api/test_recompute_endpoint.py`

### Modify
- `infrastructure/db/models.py` — `EntityEvent` ORM class
- `layers/risk/workflow.py` — accept a `signal_filter: Optional[set[str]]` parameter
- `infrastructure/db/grade_calibration_store.py` — when `record_human_verdict` records a disagreement, enqueue a dispatcher event

## Migration `028`

```python
"""V7 Phase 13 — entity_events table for delta-aware recompute.

Revision ID: 028
Revises: 027
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "028"
down_revision = "027"


def upgrade():
    op.create_table(
        "entity_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source_feed", sa.String(64), nullable=False),
        sa.Column("dedup_key", sa.String(128), nullable=True, unique=True),  # e.g. SEC accession number
        sa.Column("payload", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blast_radius", JSONB, server_default=sa.text("'[]'::jsonb")),  # list[signal_id]
        sa.Column("resulting_model_version_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_entity_events_entity_received", "entity_events", ["entity_id", "received_at"])
    op.create_index("ix_entity_events_type_received", "entity_events", ["event_type", "received_at"])
    op.create_index("ix_entity_events_dispatched", "entity_events", ["dispatched_at"])


def downgrade():
    op.drop_index("ix_entity_events_dispatched", table_name="entity_events")
    op.drop_index("ix_entity_events_type_received", table_name="entity_events")
    op.drop_index("ix_entity_events_entity_received", table_name="entity_events")
    op.drop_table("entity_events")
```

## Dependency graph

`infrastructure/recompute/signal_deps.py`:

```python
"""V7 Phase 13 — declarative signal dependency graph.

Each entry says:
    triggers      — which entity-event types cause this signal to be re-extracted
    depends_on    — which other signals' values feed into this signal

CI lint asserts every signal_id in the signal_registry is present here.
"""
from __future__ import annotations

from typing import TypedDict


class SignalDep(TypedDict):
    triggers: list[str]
    depends_on: list[str]


SIGNAL_DEPS: dict[str, SignalDep] = {
    "sanctions_screening_result": {
        "triggers": ["sanctions_update", "manual_recompute", "human_calibration_disagreement"],
        "depends_on": [],
    },
    "director_litigation_history": {
        "triggers": ["entity_directorship", "manual_recompute"],
        "depends_on": [],
    },
    "sec_filing_recency": {
        "triggers": ["entity_filing", "manual_recompute"],
        "depends_on": [],
    },
    "esg_score": {
        "triggers": ["manual_recompute"],
        "depends_on": ["sentiment_30d", "regulatory_actions_24m"],
    },
    # ... fill in for every signal_id in the registry ...
}


def triggers_for(event_type: str) -> set[str]:
    """All signal_ids that name this event_type as a trigger."""
    return {sid for sid, dep in SIGNAL_DEPS.items() if event_type in dep["triggers"]}


def downstream_of(signal_id: str) -> set[str]:
    """Transitive closure: every signal that lists signal_id in its depends_on."""
    closure: set[str] = set()
    pending = {signal_id}
    while pending:
        sid = pending.pop()
        for downstream, dep in SIGNAL_DEPS.items():
            if sid in dep["depends_on"] and downstream not in closure:
                closure.add(downstream)
                pending.add(downstream)
    return closure
```

CI lint: `tests/unit/test_signal_deps_lint.py` loads every coverage's `signal_registry` and asserts every `signal_id` appears in `SIGNAL_DEPS`. (Note: signal IDs are coverage-scoped; the lint runs per-coverage.)

## Blast radius

`infrastructure/recompute/blast_radius.py`:

```python
from __future__ import annotations

from .signal_deps import SIGNAL_DEPS, downstream_of, triggers_for


def compute_blast_radius(*, event_type: str, hinted_signal_id: str | None) -> set[str]:
    """Given an event type (and optional explicit signal), return the set of
    signals to re-extract.

    Composition:
        1. Direct triggers — signals whose `triggers` includes event_type.
        2. Hinted signal (if any).
        3. Transitive downstream closure of (1) + (2).
    """
    direct = triggers_for(event_type)
    if hinted_signal_id and hinted_signal_id in SIGNAL_DEPS:
        direct.add(hinted_signal_id)
    closure = set(direct)
    for sid in list(direct):
        closure |= downstream_of(sid)
    return closure
```

## Dispatcher

`infrastructure/recompute/dispatcher.py`:

```python
"""V7 Phase 13 — receive event → compute blast radius → invoke targeted workflow."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.db.compliance_audit_store import log_event
from infrastructure.db.models import EntityEvent
from infrastructure.recompute.blast_radius import compute_blast_radius


_RATE_WINDOW = timedelta(hours=1)


def receive_event(
    db: Session,
    *,
    event_type: str,
    source_feed: str,
    entity_id: str,
    payload: dict,
    dedup_key: Optional[str] = None,
    submission_id: Optional[uuid.UUID] = None,
    hinted_signal_id: Optional[str] = None,
) -> EntityEvent:
    if dedup_key:
        existing = db.query(EntityEvent).filter_by(dedup_key=dedup_key).one_or_none()
        if existing is not None:
            return existing
    blast = sorted(compute_blast_radius(event_type=event_type, hinted_signal_id=hinted_signal_id))
    row = EntityEvent(
        event_type=event_type,
        source_feed=source_feed,
        entity_id=entity_id,
        submission_id=submission_id,
        dedup_key=dedup_key,
        payload=payload,
        blast_radius=blast,
    )
    db.add(row)
    db.flush()
    log_event(db, event_type="entity_event_received", submission_id=submission_id,
              payload={"entity_id": entity_id, "event_type": event_type, "blast_size": len(blast)})
    return row


def dispatch_due(db: Session, *, workflow, now: datetime | None = None) -> int:
    """Iterate undispatched events; for each, run a targeted recompute respecting rate window.

    Designed to be called from an existing background worker.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - _RATE_WINDOW
    q = db.query(EntityEvent).filter(EntityEvent.dispatched_at.is_(None)).order_by(EntityEvent.received_at.asc())
    dispatched = 0
    seen_pairs: set[tuple[str, str]] = set()
    for ev in q.all():
        recent = (
            db.query(EntityEvent)
            .filter(
                EntityEvent.entity_id == ev.entity_id,
                EntityEvent.dispatched_at.isnot(None),
                EntityEvent.dispatched_at >= cutoff,
            )
            .count()
        )
        if recent:
            continue
        blast = set(ev.blast_radius or [])
        log_event(db, event_type="delta_recompute_started", submission_id=ev.submission_id,
                  payload={"entity_id": ev.entity_id, "signals": sorted(blast)})
        new_mv_id = workflow.run_targeted(
            submission_id=ev.submission_id,
            entity_id=ev.entity_id,
            signal_filter=blast,
            triggered_by_event_id=ev.id,
        )
        ev.dispatched_at = datetime.now(timezone.utc)
        ev.resulting_model_version_id = new_mv_id
        dispatched += 1
        log_event(db, event_type="delta_recompute_completed",
                  submission_id=ev.submission_id, model_version_id=new_mv_id,
                  payload={"event_id": str(ev.id), "signals": sorted(blast)})
    return dispatched
```

## Workflow change

`layers/risk/workflow.py`:

```python
def run_targeted(
    self,
    *,
    submission_id,
    entity_id,
    signal_filter: set[str] | None,
    triggered_by_event_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Run a delta cycle. Only `signal_filter` signals are re-extracted; the
    rest are copied from the previous ModelVersion. Composite rollup,
    referral evaluation, and commit run over the merged signal set.

    Returns the new ModelVersion.id.
    """
    prev_mv = self._latest_model_version(submission_id)
    re_extract_set = signal_filter or set()
    re_results = {sid: self._run_inference_for(sid, entity_id) for sid in re_extract_set}
    copied = {
        sid: self._copy_signal_from(prev_mv, sid)
        for sid in prev_mv.signal_ids if sid not in re_extract_set
    }
    merged = {**copied, **re_results}
    return self._score_validate_commit(
        submission_id=submission_id,
        entity_id=entity_id,
        signal_results=merged,
        version_type="delta_recompute",
        triggered_by_event_id=triggered_by_event_id,
    )
```

## Webhook router

`infrastructure/api/routes/events.py`:

```python
"""V7 Phase 13 — external-feed webhook receivers.

Each adapter is responsible for HMAC verification and payload normalisation
into the dispatcher's `receive_event` signature.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from infrastructure.api.utils import get_db
from infrastructure.recompute.adapters import sec_edgar, companies_house, ofac
from infrastructure.recompute.dispatcher import receive_event


router = APIRouter(prefix="/api/v1/events/external", tags=["events"])


@router.post("/sec_edgar")
async def sec_edgar_webhook(req: Request, x_signature: str = Header(...), db: Session = Depends(get_db)):
    raw = await req.body()
    if not sec_edgar.verify_hmac(raw, x_signature):
        raise HTTPException(401, "invalid signature")
    payload = sec_edgar.parse(raw)
    receive_event(db, **payload)
    db.commit()
    return {"ok": True}


@router.post("/companies_house")
async def companies_house_webhook(req: Request, x_signature: str = Header(...), db: Session = Depends(get_db)):
    raw = await req.body()
    if not companies_house.verify_hmac(raw, x_signature):
        raise HTTPException(401, "invalid signature")
    payload = companies_house.parse(raw)
    receive_event(db, **payload)
    db.commit()
    return {"ok": True}


@router.post("/ofac")
async def ofac_webhook(req: Request, x_signature: str = Header(...), db: Session = Depends(get_db)):
    raw = await req.body()
    if not ofac.verify_hmac(raw, x_signature):
        raise HTTPException(401, "invalid signature")
    payload = ofac.parse(raw)
    receive_event(db, **payload)
    db.commit()
    return {"ok": True}
```

## Manual recompute API

`infrastructure/api/routes/recompute.py`:

```python
"""V7 Phase 13 — manual delta-recompute endpoint."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from infrastructure.api.utils import get_db, current_user
from infrastructure.recompute.dispatcher import receive_event


router = APIRouter(prefix="/api/v1/recompute", tags=["recompute"])


class ManualRequest(BaseModel):
    submission_id: uuid.UUID
    signal_ids: List[str] = []
    primitive_types: List[str] = []


@router.post("")
def manual_recompute(body: ManualRequest, db=Depends(get_db), user=Depends(current_user)):
    if not body.signal_ids and not body.primitive_types:
        raise HTTPException(400, "supply signal_ids and/or primitive_types")
    # Map primitive_types → signal_ids via the registry for this submission's coverage.
    entity_id = ...  # resolve from submission
    receive_event(
        db, event_type="manual_recompute", source_feed="manual",
        entity_id=entity_id, submission_id=body.submission_id,
        payload={"signal_ids": body.signal_ids, "primitive_types": body.primitive_types,
                 "requested_by": str(user.id)},
        # hinted_signal_id: pass the first one if any, dispatcher widens via closure
        hinted_signal_id=(body.signal_ids[0] if body.signal_ids else None),
    )
    db.commit()
    return {"ok": True}
```

## Calibration disagreement hook

`infrastructure/db/grade_calibration_store.py` (modify `record_human_verdict`):

```python
from infrastructure.recompute.dispatcher import receive_event

def record_human_verdict(db, *, sample_id, human_grade, decided_by, note=""):
    # ... existing code ...
    if not exact_e:
        # Disagreement: queue a targeted recompute of that signal
        receive_event(
            db, event_type="human_calibration_disagreement",
            source_feed="calibration_internal",
            entity_id=...,  # resolved via sample → submission → entity
            submission_id=sample.submission_id,
            payload={"sample_id": str(sample.id), "human_grade": human_grade,
                     "extractor_grade": sample.extractor_grade},
            hinted_signal_id=sample.signal_id,
        )
```

## Steps

### 13.1 — Migration
**File**: `alembic/versions/028_entity_events.py`. Apply + round-trip.

### 13.2 — ORM
**File**: `infrastructure/db/models.py`. Add `EntityEvent`.

### 13.3 — Dependency graph + lint
**Files**: `infrastructure/recompute/signal_deps.py`, `tests/unit/test_signal_deps_lint.py`.
**Action**: Author the dep graph for every signal in the registry. Lint test scans every coverage's `signal_registry` and asserts presence in `SIGNAL_DEPS`.

### 13.4 — Blast radius + dispatcher
**Files**: `blast_radius.py`, `dispatcher.py`.
**Test**: Synthetic events → expected blast set; rate window honoured.

### 13.5 — Webhook adapters (stubs)
**Files**: `adapters/{sec_edgar,companies_house,ofac}.py`.
**Action**: Implement `verify_hmac` and `parse` stubs. Tests use a fixed HMAC secret + crafted payloads to assert verification + parsing logic.

### 13.6 — Routes
**Files**: `routes/events.py`, `routes/recompute.py`.
**Action**: Register in `infrastructure/api/main.py`.

### 13.7 — Workflow.run_targeted
**File**: `layers/risk/workflow.py`.
**Action**: Implement the delta cycle: copy unchanged signals from prev mv, re-extract filter, score, validate, rollup, commit with `version_type="delta_recompute"` and `triggered_by_event_id` set.

### 13.8 — Calibration hook
**File**: `infrastructure/db/grade_calibration_store.py`.
**Action**: On disagreement decision, queue a `human_calibration_disagreement` event.

### 13.9 — Background worker
**File**: existing worker harness in `infrastructure/workers/`.
**Action**: Add a periodic task that calls `dispatcher.dispatch_due` every 30 seconds. Out of scope for this phase to deploy; phase ships the function, deploy is platform-team work.

## Test gates

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head

pytest tests/unit/test_blast_radius.py tests/unit/test_signal_deps_lint.py -v
pytest tests/api/test_events_webhook.py tests/api/test_recompute_endpoint.py -v

# End-to-end: post a synthetic sec_edgar webhook; assert one EntityEvent stored,
# blast radius computed, dispatcher creates a new ModelVersion with version_type="delta_recompute".
pytest tests/integration/test_delta_recompute_e2e.py -v

# Calibration unchanged. Delta recompute produces the same numbers as full recompute
# when blast_radius covers all signals.
python -m layers.risk.calibration_harness fi cyber casualty
```

## Done when

- [ ] Every signal in every coverage's registry has a `SIGNAL_DEPS` entry (lint enforces).
- [ ] Webhook routers verify HMAC and parse payloads.
- [ ] Dispatcher computes blast radius, respects rate window, creates a new ModelVersion.
- [ ] Manual `/api/v1/recompute` endpoint works; rejects empty filters.
- [ ] Calibration disagreement queues a targeted recompute.
- [ ] Delta recompute produces a ModelVersion with `version_type="delta_recompute"` and `triggered_by_event_id` set.
- [ ] Full pytest green.

## Out of scope

- Live integration with real SEC / Companies House / OFAC feeds — adapters are stubs.
- Dynamic dependency-graph editing UI. → V8.
- Background worker deployment. → Platform.

## Invariants

1. Every undispatched event eventually dispatches (no orphan rows).
2. Within a 1-hour window, at most one delta recompute fires per (entity, signal) pair.
3. Delta recompute copies unchanged signals from the previous ModelVersion; signal_history grows by exactly the blast-radius count, not the full registry count.
4. Composite rollup, referrals, validator, calibration sampling all run on the merged set.
5. No pricing impact except where genuine new evidence arrives via the event.
