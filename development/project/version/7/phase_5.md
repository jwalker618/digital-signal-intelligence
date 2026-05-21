# V7 Phase 5: Persistence — History, Commitments, Dual Audit

## Depends on
- Phase 2 (every produced signal carries a grade).
- Phase 3 (composite + group rollups exist on `ScoringResult`).
- Phase 4 (grade-driven referrals exist on `triggered_conditions`).

## Blocks
- Phase 6 (validator records its verdict; persistence must accept it).
- Phase 7 (calibration store joins to historical grade rows).
- Phase 14 (API exposes persisted fields).

## Scope

Three orthogonal persistence concerns land together because they share migration ergonomics:

1. **Evidence columns** — `signal_results` (via `ModelVersionSignal`) and `model_versions` gain grade/basis/sources columns + the composite rollup.
2. **Append-only signal history** — new `signal_history` table records every per-cycle `SignalResult` with its grade, basis, sources, and pro/counter/tie-breaker. Solves the "no grade revision/history" review concern.
3. **Cryptographic commitments** — new `signal_commitments` table stores SHA3-224 digests of canonical-JSON signal payloads at cycle commit time. Defensible "we knew this before we priced it" trail.
4. **Dual audit log** — split the existing `AuditLog` into operational vs compliance lanes. Existing rows stay in `audit_logs`; new `compliance_audit_logs` table carries grade-relevant events.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | New alembic revision | `023_evidence_grade.py` (next sequential; existing latest is 022) |
| D2 | Columns on `model_version_signals` | `evidence_grade VARCHAR(32) NULL`, `evidence_basis VARCHAR(500) NULL`, `evidence_sources JSONB DEFAULT '[]'`, `evidence_pro TEXT NULL`, `evidence_counter TEXT NULL`, `evidence_tie_breaker TEXT NULL`, `absence_sub_type VARCHAR(32) NULL` |
| D3 | Columns on `model_versions` | `composite_min_grade VARCHAR(32) NULL`, `composite_weighted_mean_grade NUMERIC(4,2) NULL`, `composite_grade_distribution JSONB DEFAULT '{}'` |
| D4 | History table | `signal_history` — append-only, primary key `(model_version_id, signal_id, recorded_at)`. Insert on every cycle, never update. Indexed on `(submission_id, signal_id)` |
| D5 | Commitment table | `signal_commitments` — `(commitment_id PK, model_version_id FK, scope, digest, algorithm, committed_at)`. `scope` in `{full_payload, value_and_grade, pro_counter}`. Algorithm fixed to `sha3_224` |
| D6 | Canonical JSON | `json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)` — same shape used by existing `provenance.py:_canonical_bytes` |
| D7 | Dual audit | `audit_logs` unchanged. New `compliance_audit_logs` table for grade-policy decisions: grade-referrals fired, policy-rule activated, expected-grade violation, validator verdict (Phase 6 writes here) |
| D8 | Backfill | Existing `model_version_signals` rows: `evidence_grade=NULL`, `evidence_basis='Pre-V7 record; grade not captured'` for rows committed before this migration's timestamp. No backfill from history reconstruction |
| D9 | NOT NULL deferred | Columns stay nullable in this migration. Phase 6 migration `024` tightens `evidence_grade NOT NULL` once the validator has run across the full seed dataset |
| D10 | Repositories | New repository module `infrastructure/db/evidence_store.py` for grade reads/writes; existing repositories unchanged |

## Files

### Create
- `alembic/versions/023_evidence_grade.py`
- `infrastructure/db/evidence_store.py`
- `infrastructure/db/commitment_store.py`
- `infrastructure/db/compliance_audit_store.py`
- `tests/unit/test_alembic_023.py`
- `tests/unit/test_evidence_store.py`
- `tests/unit/test_commitment_store.py`
- `tests/unit/test_compliance_audit_store.py`

### Modify
- `infrastructure/db/models.py` — extend `ModelVersionSignal`, `ModelVersionRecord` with new columns; add `SignalHistory`, `SignalCommitment`, `ComplianceAuditLog` ORM classes
- `infrastructure/db/repositories.py` — wire the new stores
- `layers/risk/workflow.py` (or wherever a cycle is committed) — call the commitment generator at cycle end

## Migration

`alembic/versions/023_evidence_grade.py`:

```python
"""V7 Phase 5 — evidence-grade persistence: columns, history table,
commitments, dual audit log.

Revision ID: 023
Revises: 022
Create Date: 2026-05-XX
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "023"
down_revision: str = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Columns on model_version_signals ---------------------------------
    op.add_column("model_version_signals", sa.Column("evidence_grade", sa.String(32), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_basis", sa.String(500), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_sources", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("model_version_signals", sa.Column("evidence_pro", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_counter", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_tie_breaker", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("absence_sub_type", sa.String(32), nullable=True))
    op.create_index("ix_mvs_evidence_grade", "model_version_signals", ["evidence_grade"])

    # --- Columns on model_versions ----------------------------------------
    op.add_column("model_versions", sa.Column("composite_min_grade", sa.String(32), nullable=True))
    op.add_column("model_versions", sa.Column("composite_weighted_mean_grade", sa.Numeric(4, 2), nullable=True))
    op.add_column("model_versions", sa.Column("composite_grade_distribution", JSONB, server_default=sa.text("'{}'::jsonb")))

    # --- signal_history (append-only) -------------------------------------
    op.create_table(
        "signal_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_grade", sa.String(32), nullable=True),
        sa.Column("evidence_basis", sa.String(500), nullable=True),
        sa.Column("evidence_sources", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence_pro", sa.Text(), nullable=True),
        sa.Column("evidence_counter", sa.Text(), nullable=True),
        sa.Column("evidence_tie_breaker", sa.Text(), nullable=True),
        sa.Column("absence_sub_type", sa.String(32), nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_signal_history_submission_signal", "signal_history", ["submission_id", "signal_id"])
    op.create_index("ix_signal_history_recorded_at", "signal_history", ["recorded_at"])
    op.create_unique_constraint(
        "uq_signal_history_per_mv_signal",
        "signal_history",
        ["model_version_id", "signal_id", "recorded_at"],
    )

    # --- signal_commitments ----------------------------------------------
    op.create_table(
        "signal_commitments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=True),  # null for composite-scoped commitment
        sa.Column("scope", sa.String(32), nullable=False),  # full_payload | value_and_grade | pro_counter | composite
        sa.Column("algorithm", sa.String(16), nullable=False, server_default=sa.text("'sha3_224'")),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("canonical_keys", JSONB, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_index("ix_commitments_mv", "signal_commitments", ["model_version_id"])
    op.create_unique_constraint(
        "uq_commitment_per_mv_signal_scope",
        "signal_commitments",
        ["model_version_id", "signal_id", "scope"],
    )

    # --- compliance_audit_logs -------------------------------------------
    op.create_table(
        "compliance_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("model_version_id", UUID(as_uuid=True), nullable=True),
        sa.Column("submission_id", UUID(as_uuid=True), nullable=True),
        sa.Column("signal_id", sa.String(128), nullable=True),
        sa.Column("actor", sa.String(128), nullable=True),  # "system", user uuid str, validator-llm-id
        sa.Column("payload", JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_comp_audit_event_type", "compliance_audit_logs", ["event_type"])
    op.create_index("ix_comp_audit_submission", "compliance_audit_logs", ["submission_id"])

    # --- Backfill existing model_version_signals --------------------------
    op.execute(
        "UPDATE model_version_signals "
        "SET evidence_basis = 'Pre-V7 record; grade not captured' "
        "WHERE evidence_basis IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_comp_audit_submission", table_name="compliance_audit_logs")
    op.drop_index("ix_comp_audit_event_type", table_name="compliance_audit_logs")
    op.drop_table("compliance_audit_logs")

    op.drop_constraint("uq_commitment_per_mv_signal_scope", "signal_commitments", type_="unique")
    op.drop_index("ix_commitments_mv", table_name="signal_commitments")
    op.drop_table("signal_commitments")

    op.drop_constraint("uq_signal_history_per_mv_signal", "signal_history", type_="unique")
    op.drop_index("ix_signal_history_recorded_at", table_name="signal_history")
    op.drop_index("ix_signal_history_submission_signal", table_name="signal_history")
    op.drop_table("signal_history")

    op.drop_column("model_versions", "composite_grade_distribution")
    op.drop_column("model_versions", "composite_weighted_mean_grade")
    op.drop_column("model_versions", "composite_min_grade")

    op.drop_index("ix_mvs_evidence_grade", table_name="model_version_signals")
    op.drop_column("model_version_signals", "absence_sub_type")
    op.drop_column("model_version_signals", "evidence_tie_breaker")
    op.drop_column("model_version_signals", "evidence_counter")
    op.drop_column("model_version_signals", "evidence_pro")
    op.drop_column("model_version_signals", "evidence_sources")
    op.drop_column("model_version_signals", "evidence_basis")
    op.drop_column("model_version_signals", "evidence_grade")
```

## ORM additions

`infrastructure/db/models.py`:

```python
class ModelVersionSignal(Base):
    # ... existing columns ...
    evidence_grade = Column(String(32), nullable=True)
    evidence_basis = Column(String(500), nullable=True)
    evidence_sources = Column(JSONB, default=list)
    evidence_pro = Column(Text(), nullable=True)
    evidence_counter = Column(Text(), nullable=True)
    evidence_tie_breaker = Column(Text(), nullable=True)
    absence_sub_type = Column(String(32), nullable=True)


class ModelVersionRecord(Base):
    # ... existing columns ...
    composite_min_grade = Column(String(32), nullable=True)
    composite_weighted_mean_grade = Column(Numeric(4, 2), nullable=True)
    composite_grade_distribution = Column(JSONB, default=dict)


class SignalHistory(Base):
    __tablename__ = "signal_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(String(128), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    score = Column(Float(), nullable=True)
    category = Column(String(128), nullable=True)
    confidence = Column(Float(), nullable=True)
    evidence_grade = Column(String(32), nullable=True)
    evidence_basis = Column(String(500), nullable=True)
    evidence_sources = Column(JSONB, default=list)
    evidence_pro = Column(Text(), nullable=True)
    evidence_counter = Column(Text(), nullable=True)
    evidence_tie_breaker = Column(Text(), nullable=True)
    absence_sub_type = Column(String(32), nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)


class SignalCommitment(Base):
    __tablename__ = "signal_commitments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    signal_id = Column(String(128), nullable=True)
    scope = Column(String(32), nullable=False)
    algorithm = Column(String(16), nullable=False, default="sha3_224")
    digest = Column(String(64), nullable=False)
    committed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    canonical_keys = Column(JSONB, default=list)


class ComplianceAuditLog(Base):
    __tablename__ = "compliance_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(64), nullable=False)
    event_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    model_version_id = Column(UUID(as_uuid=True), nullable=True)
    submission_id = Column(UUID(as_uuid=True), nullable=True)
    signal_id = Column(String(128), nullable=True)
    actor = Column(String(128), nullable=True)
    payload = Column(JSONB, default=dict)
```

## Commitment store

`infrastructure/db/commitment_store.py`:

```python
"""V7 Phase 5 — SHA3-224 commitments over canonical-JSON payloads.

Modelled on signal_architecture/signals/provenance.py's canonicalisation
to keep digest comparisons interoperable. Three commitment scopes:

    full_payload     — entire SignalResult dict
    value_and_grade  — minimum tuple sufficient to dispute later
    pro_counter      — pro/counter/tie-breaker text only (Phase 6 writes these)
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.orm import Session

from infrastructure.db.models import SignalCommitment
from signal_architecture.signals.types import SignalResult


CommitmentScope = Literal["full_payload", "value_and_grade", "pro_counter", "composite"]


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha3_224(payload: Any) -> str:
    return hashlib.sha3_224(_canonical_bytes(payload)).hexdigest()


def _payload_for_scope(sig: SignalResult, scope: CommitmentScope) -> tuple[dict[str, Any], list[str]]:
    """Return (canonical_payload, key_list) for the given scope."""
    if scope == "full_payload":
        keys = sorted([
            "signal_id", "score", "category", "confidence",
            "evidence_grade", "evidence_basis",
            "evidence_pro", "evidence_counter", "evidence_tie_breaker",
            "absence_sub_type",
        ])
        payload = {k: getattr(sig, k, None) for k in keys}
        # sources serialised separately to keep this stable
        payload["evidence_sources"] = [s.to_dict() for s in (sig.evidence_sources or [])]
        return payload, keys + ["evidence_sources"]
    if scope == "value_and_grade":
        keys = ["signal_id", "score", "category", "evidence_grade"]
        return {k: getattr(sig, k, None) for k in keys}, keys
    if scope == "pro_counter":
        keys = ["signal_id", "evidence_pro", "evidence_counter", "evidence_tie_breaker"]
        return {k: getattr(sig, k, None) for k in keys}, keys
    raise ValueError(f"unknown scope: {scope}")


def commit_signal(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    sig: SignalResult,
    scope: CommitmentScope = "full_payload",
) -> str:
    """Hash and persist. Returns the hex digest."""
    payload, keys = _payload_for_scope(sig, scope)
    digest = sha3_224(payload)
    row = SignalCommitment(
        model_version_id=model_version_id,
        signal_id=sig.signal_id,
        scope=scope,
        algorithm="sha3_224",
        digest=digest,
        committed_at=datetime.now(timezone.utc),
        canonical_keys=keys,
    )
    db.add(row)
    return digest


def commit_composite(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    composite_min_grade: str | None,
    composite_weighted_mean_grade: float | None,
    composite_grade_distribution: dict[str, float],
    referral_reasons: list[str],
) -> str:
    payload = {
        "composite_min_grade": composite_min_grade,
        "composite_weighted_mean_grade": composite_weighted_mean_grade,
        "composite_grade_distribution": composite_grade_distribution,
        "referral_reasons": sorted(referral_reasons),
    }
    digest = sha3_224(payload)
    row = SignalCommitment(
        model_version_id=model_version_id,
        signal_id=None,
        scope="composite",
        algorithm="sha3_224",
        digest=digest,
        committed_at=datetime.now(timezone.utc),
        canonical_keys=sorted(payload.keys()),
    )
    db.add(row)
    return digest


def verify(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    signal_id: str | None,
    scope: CommitmentScope,
    candidate_payload: dict[str, Any],
) -> bool:
    """True if the stored digest matches the candidate's canonical hash."""
    row = (
        db.query(SignalCommitment)
        .filter_by(model_version_id=model_version_id, signal_id=signal_id, scope=scope)
        .one_or_none()
    )
    if row is None:
        return False
    return row.digest == sha3_224(candidate_payload)
```

## Evidence store

`infrastructure/db/evidence_store.py`:

```python
"""V7 Phase 5 — read/write helpers for evidence columns + signal_history."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import ModelVersionSignal, SignalHistory
from signal_architecture.signals.types import SignalResult


def persist_signal_evidence(
    db: Session,
    *,
    mvs_row: ModelVersionSignal,
    sig: SignalResult,
) -> None:
    """Update the ModelVersionSignal row in-place with V7 fields, and
    write an append-only SignalHistory row.
    """
    mvs_row.evidence_grade = sig.evidence_grade
    mvs_row.evidence_basis = sig.evidence_basis
    mvs_row.evidence_sources = [s.to_dict() for s in (sig.evidence_sources or [])]
    mvs_row.evidence_pro = sig.evidence_pro
    mvs_row.evidence_counter = sig.evidence_counter
    mvs_row.evidence_tie_breaker = sig.evidence_tie_breaker
    mvs_row.absence_sub_type = sig.absence_sub_type

    db.add(SignalHistory(
        model_version_id=mvs_row.model_version_id,
        submission_id=mvs_row.submission_id,
        signal_id=sig.signal_id,
        recorded_at=datetime.now(timezone.utc),
        score=sig.score,
        category=sig.category,
        confidence=sig.confidence,
        evidence_grade=sig.evidence_grade,
        evidence_basis=sig.evidence_basis,
        evidence_sources=[s.to_dict() for s in (sig.evidence_sources or [])],
        evidence_pro=sig.evidence_pro,
        evidence_counter=sig.evidence_counter,
        evidence_tie_breaker=sig.evidence_tie_breaker,
        absence_sub_type=sig.absence_sub_type,
        metadata_=sig.metadata or {},
    ))
```

## Compliance audit store

`infrastructure/db/compliance_audit_store.py`:

```python
"""V7 Phase 5 — compliance-grade audit log (separate from operational AuditLog).

Emitted events (canonical event_type strings):

    evidence_grade_referral_fired
    evidence_grade_policy_evaluated
    expected_grade_violation
    validator_verdict          # Phase 6 writes here
    calibration_sample_logged  # Phase 7 writes here
    commitment_committed
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import ComplianceAuditLog


def log_event(
    db: Session,
    *,
    event_type: str,
    payload: dict[str, Any],
    model_version_id: Optional[uuid.UUID] = None,
    submission_id: Optional[uuid.UUID] = None,
    signal_id: Optional[str] = None,
    actor: str = "system",
) -> None:
    db.add(ComplianceAuditLog(
        event_type=event_type,
        model_version_id=model_version_id,
        submission_id=submission_id,
        signal_id=signal_id,
        actor=actor,
        payload=payload,
    ))
```

## Steps

### 5.1 — Migration
**File**: `alembic/versions/023_evidence_grade.py` (create).
**Action**: Drop in the migration above. Run `alembic upgrade head` against a test DB; assert all tables/columns/indexes/constraints present. Run `alembic downgrade -1` and assert clean tear-down.

### 5.2 — ORM
**File**: `infrastructure/db/models.py`.
**Action**: Extend `ModelVersionSignal` and `ModelVersionRecord`; add `SignalHistory`, `SignalCommitment`, `ComplianceAuditLog` classes.

### 5.3 — Stores
**Files**: `infrastructure/db/evidence_store.py`, `commitment_store.py`, `compliance_audit_store.py` (create).
**Action**: Drop in modules.

### 5.4 — Wire into workflow
**File**: `layers/risk/workflow.py` (or wherever a model cycle is committed today).
**Action**: At cycle commit:
1. For each signal result, call `persist_signal_evidence(db, mvs_row=..., sig=...)`.
2. For each signal, call `commitment_store.commit_signal(db, model_version_id=..., sig=..., scope="value_and_grade")`. Composite-scope commitment via `commit_composite(...)`.
3. For each grade-driven `TriggeredCondition`, call `compliance_audit_store.log_event(event_type="evidence_grade_referral_fired", payload=...)`.

### 5.5 — Tests
**Files**:
- `tests/unit/test_alembic_023.py` — up/down roundtrip in sqlite-or-postgres test container.
- `tests/unit/test_evidence_store.py` — `persist_signal_evidence` updates row + appends history.
- `tests/unit/test_commitment_store.py` — same canonical payload → same digest; modified payload → `verify` returns False; canonical key reordering doesn't change digest.
- `tests/unit/test_compliance_audit_store.py` — events landed with correct `event_type` and payload.

## Test gates

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head

pytest tests/unit/test_alembic_023.py \
        tests/unit/test_evidence_store.py \
        tests/unit/test_commitment_store.py \
        tests/unit/test_compliance_audit_store.py -v

pytest tests/ -x -q

# Integration: seed a fresh DB, run one cycle, assert rows landed
python -m seed bench
psql -c "SELECT COUNT(*) FROM signal_history WHERE evidence_grade IS NOT NULL"
psql -c "SELECT COUNT(*) FROM signal_commitments"
psql -c "SELECT event_type, COUNT(*) FROM compliance_audit_logs GROUP BY event_type"
```

## Done when

- [ ] `alembic upgrade head` clean; downgrade clean.
- [ ] Cycle commit writes evidence columns, history rows, commitments, audit-log entries.
- [ ] `verify(...)` round-trip works on a real commitment.
- [ ] Backfill applied: every pre-V7 row has `evidence_basis='Pre-V7 record; grade not captured'`.
- [ ] No NOT NULL constraint on `evidence_grade` yet (Phase 6 tightens).
- [ ] Full pytest green.

## Out of scope

- NOT NULL on `evidence_grade`. → Phase 6 (alembic 024) after validator has run on every signal.
- Validator verdict persistence rows. → Phase 6 schema lives on top of `ComplianceAuditLog` and a new `validator_verdicts` table introduced there.
- API/Pydantic exposure. → Phase 14.

## Invariants

1. `signal_history` is append-only — no application code issues `UPDATE` or `DELETE` against it (enforced by code review; consider a `BEFORE UPDATE OR DELETE` trigger in Phase 7 if desired).
2. Commitments are deterministic: same canonical payload → same SHA3-224 hex.
3. `commitment_keys` records exactly which fields participated in the digest, so a future schema change cannot silently invalidate verification.
4. `compliance_audit_logs` is separate from operational `audit_logs`; nothing writes to both for the same event.
