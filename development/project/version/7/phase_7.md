# V7 Phase 7: Grade Calibration Store (Human-in-the-Loop)

## Depends on
- Phase 5 (`compliance_audit_logs`, `signal_history`).
- Phase 6 (validator verdicts persisted; pro/counter/tie-breaker populated).

## Blocks
- Phase 14 (UI surface for the calibration queue).

## Scope

Build a longitudinal calibration store that records **three** grade verdicts per sampled signal — extractor, validator, human — and computes agreement rates over time. Target: 89% exact match (the Clearwing reference benchmark). Sampling strategy: every high-weight signal in a referred submission, plus a stratified random sample across grades. UI for human verdict capture is land via Phase 14; this phase lands the data plane, scheduler, and an API endpoint for the underwriter calibration queue.

This is the trust-with-underwriters layer. Phase 6 measures machine-vs-machine; this phase measures machine-vs-human and drives the back-pressure loop.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Triple | `extractor_grade`, `validator_grade`, `human_grade` per sampled `(model_version_id, signal_id)` |
| D2 | Sampling | All signals with weight≥0.10 in submissions where any grade-driven referral fired, plus 5% stratified random sample over signals with weight≥0.05 |
| D3 | Stratification | By (coverage, evidence_grade) — five quintiles per coverage so no rung is starved |
| D4 | Metrics | `exact_match_rate` (extractor==human), `validator_match_rate` (validator==human), `within_one_rate` (|rank diff| ≤ 1). Computed over rolling 30-day and lifetime windows |
| D5 | Storage | New `grade_calibration_samples` table, append-only, plus a `grade_calibration_decisions` table for human verdicts |
| D6 | Human-verdict capture | API endpoint `POST /api/v1/calibration/decision` accepts `{sample_id, human_grade, note, decided_by}`. Phase 14 builds the UI |
| D7 | Idempotency | `(model_version_id, signal_id)` unique on `grade_calibration_samples` — re-sampling the same signal is a no-op |
| D8 | Latency tolerance | Human verdict may arrive days after sample creation. Sample lifecycle states: `pending`, `decided`, `expired` (>90 days without decision) |
| D9 | Drift alerts | If 30-day rolling `exact_match_rate` drops below `calibration_floor` (default 0.75), emit a `WeDriftAlert` (existing table from V6) with `category="grade_calibration_drift"` |
| D10 | Sampling scheduler | Runs at cycle commit (synchronous, cheap — just inserts rows). No background job needed in V7. Phase 11 may externalise |

## Files

### Create
- `alembic/versions/025_grade_calibration.py`
- `infrastructure/db/grade_calibration_store.py`
- `infrastructure/api/routes/grade_calibration.py`
- `infrastructure/api/types_calibration.py` (Pydantic DTOs)
- `signal_architecture/validation/sampler.py` — stratified sampler
- `tests/unit/test_grade_calibration_sampler.py`
- `tests/unit/test_grade_calibration_store.py`
- `tests/api/test_grade_calibration_endpoint.py`

### Modify
- `infrastructure/db/models.py` — `GradeCalibrationSample`, `GradeCalibrationDecision` ORM classes
- `layers/risk/workflow.py` — invoke sampler at cycle commit
- `infrastructure/api/main.py` — register new router

## Migration `025`

```python
"""V7 Phase 7 — grade calibration samples + human decisions.

Revision ID: 025
Revises: 024
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "025"
down_revision = "024"

def upgrade():
    op.create_table(
        "grade_calibration_samples",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coverage", sa.String(64), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("signal_weight", sa.Float, nullable=False),
        sa.Column("extractor_grade", sa.String(32), nullable=False),
        sa.Column("validator_grade", sa.String(32), nullable=True),
        sa.Column("sampling_reason", sa.String(64), nullable=False),  # high_weight_referred | stratified_random
        sa.Column("state", sa.String(16), nullable=False, server_default=sa.text("'pending'")),  # pending | decided | expired
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint(
        "uq_calibration_sample_per_mv_signal",
        "grade_calibration_samples",
        ["model_version_id", "signal_id"],
    )
    op.create_index("ix_calibration_state", "grade_calibration_samples", ["state"])
    op.create_index("ix_calibration_coverage_grade", "grade_calibration_samples", ["coverage", "extractor_grade"])

    op.create_table(
        "grade_calibration_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("sample_id", UUID(as_uuid=True), sa.ForeignKey("grade_calibration_samples.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("human_grade", sa.String(32), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("exact_match_extractor", sa.Boolean, nullable=False),
        sa.Column("exact_match_validator", sa.Boolean, nullable=True),
        sa.Column("within_one_extractor", sa.Boolean, nullable=False),
    )
    op.create_index("ix_calibration_decision_match", "grade_calibration_decisions", ["exact_match_extractor", "decided_at"])


def downgrade():
    op.drop_index("ix_calibration_decision_match", table_name="grade_calibration_decisions")
    op.drop_table("grade_calibration_decisions")
    op.drop_index("ix_calibration_coverage_grade", table_name="grade_calibration_samples")
    op.drop_index("ix_calibration_state", table_name="grade_calibration_samples")
    op.drop_constraint("uq_calibration_sample_per_mv_signal", "grade_calibration_samples", type_="unique")
    op.drop_table("grade_calibration_samples")
```

## Sampler

`signal_architecture/validation/sampler.py`:

```python
"""V7 Phase 7 — stratified sampler that picks signals for human grade review.

Rules:
    - All signals with weight >= 0.10 in submissions where any grade-driven
      referral fired (sampling_reason='high_weight_referred').
    - Plus a stratified random sample: 5% of signals with weight >= 0.05,
      stratified by (coverage, extractor_grade) so no quintile is starved.

Deterministic seed derived from model_version_id + a phase-7 salt so
re-running gives identical samples in tests.
"""
from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable


_SALT = "v7_phase7_grade_sampler"
_EXPIRY_DAYS = 90
_HIGH_WEIGHT_FLOOR = 0.10
_STRATIFIED_FLOOR = 0.05
_STRATIFIED_RATE = 0.05


@dataclass
class SamplingCandidate:
    submission_id: uuid.UUID
    model_version_id: uuid.UUID
    coverage: str
    signal_id: str
    signal_weight: float
    extractor_grade: str
    validator_grade: str | None


@dataclass
class SamplingTarget:
    candidate: SamplingCandidate
    reason: str  # high_weight_referred | stratified_random


def _deterministic_rng(mv_id: uuid.UUID) -> random.Random:
    key = f"{_SALT}:{mv_id}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
    return random.Random(seed)


def select_targets(
    candidates: Iterable[SamplingCandidate],
    *,
    any_referral_fired: bool,
    mv_id: uuid.UUID,
) -> list[SamplingTarget]:
    candidates = list(candidates)
    out: list[SamplingTarget] = []

    if any_referral_fired:
        for c in candidates:
            if c.signal_weight >= _HIGH_WEIGHT_FLOOR:
                out.append(SamplingTarget(c, "high_weight_referred"))

    # Stratify by (coverage, extractor_grade) and take _STRATIFIED_RATE of each
    rng = _deterministic_rng(mv_id)
    buckets: dict[tuple[str, str], list[SamplingCandidate]] = {}
    for c in candidates:
        if c.signal_weight < _STRATIFIED_FLOOR:
            continue
        buckets.setdefault((c.coverage, c.extractor_grade), []).append(c)
    for bucket in buckets.values():
        rng.shuffle(bucket)
        k = max(1, int(round(_STRATIFIED_RATE * len(bucket))))
        for c in bucket[:k]:
            # Don't double-sample
            if not any(o.candidate.signal_id == c.signal_id for o in out):
                out.append(SamplingTarget(c, "stratified_random"))
    return out


def expiry_for(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now + timedelta(days=_EXPIRY_DAYS)
```

## Store

`infrastructure/db/grade_calibration_store.py`:

```python
"""V7 Phase 7 — grade-calibration data layer."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from infrastructure.db.models import GradeCalibrationSample, GradeCalibrationDecision
from signal_architecture.signals.evidence import evidence_rank


def persist_samples(db: Session, targets, mv_id: uuid.UUID, submission_id: uuid.UUID) -> int:
    """Idempotent — uses ON CONFLICT DO NOTHING via the unique constraint."""
    inserted = 0
    for t in targets:
        c = t.candidate
        existing = (
            db.query(GradeCalibrationSample)
            .filter_by(model_version_id=mv_id, signal_id=c.signal_id)
            .one_or_none()
        )
        if existing:
            continue
        db.add(GradeCalibrationSample(
            model_version_id=mv_id,
            submission_id=submission_id,
            coverage=c.coverage,
            signal_id=c.signal_id,
            signal_weight=c.signal_weight,
            extractor_grade=c.extractor_grade,
            validator_grade=c.validator_grade,
            sampling_reason=t.reason,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        ))
        inserted += 1
    return inserted


def record_human_verdict(
    db: Session, *, sample_id: uuid.UUID, human_grade: str, decided_by: uuid.UUID, note: str = "",
) -> None:
    sample = db.query(GradeCalibrationSample).get(sample_id)
    if sample is None:
        raise LookupError(f"sample {sample_id} not found")
    if sample.state != "pending":
        raise RuntimeError(f"sample {sample_id} already in state {sample.state}")
    exact_e = sample.extractor_grade == human_grade
    exact_v = (
        sample.validator_grade == human_grade if sample.validator_grade else None
    )
    within_one_e = abs(evidence_rank(sample.extractor_grade) - evidence_rank(human_grade)) <= 1

    db.add(GradeCalibrationDecision(
        sample_id=sample.id,
        human_grade=human_grade,
        note=note,
        decided_by=decided_by,
        exact_match_extractor=exact_e,
        exact_match_validator=exact_v,
        within_one_extractor=within_one_e,
    ))
    sample.state = "decided"


def expire_old(db: Session, *, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    q = db.query(GradeCalibrationSample).filter(
        GradeCalibrationSample.state == "pending",
        GradeCalibrationSample.expires_at < now,
    )
    n = q.count()
    q.update({"state": "expired"})
    return n


@dataclass
class CalibrationStats:
    window_days: int | None
    decided: int
    exact_match_extractor_rate: float
    exact_match_validator_rate: float | None
    within_one_extractor_rate: float


def stats(db: Session, *, coverage: str | None = None, window_days: int | None = 30) -> CalibrationStats:
    q = db.query(GradeCalibrationDecision)
    if window_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        q = q.filter(GradeCalibrationDecision.decided_at >= cutoff)
    if coverage is not None:
        q = q.join(GradeCalibrationSample).filter(GradeCalibrationSample.coverage == coverage)
    rows = q.all()
    if not rows:
        return CalibrationStats(window_days, 0, 0.0, None, 0.0)
    ex = sum(1 for r in rows if r.exact_match_extractor)
    v_rows = [r for r in rows if r.exact_match_validator is not None]
    v = sum(1 for r in v_rows if r.exact_match_validator)
    w1 = sum(1 for r in rows if r.within_one_extractor)
    return CalibrationStats(
        window_days=window_days,
        decided=len(rows),
        exact_match_extractor_rate=ex / len(rows),
        exact_match_validator_rate=(v / len(v_rows)) if v_rows else None,
        within_one_extractor_rate=w1 / len(rows),
    )
```

## API

`infrastructure/api/routes/grade_calibration.py`:

```python
"""V7 Phase 7 — grade calibration endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.db.grade_calibration_store import (
    record_human_verdict,
    stats as compute_stats,
)
from infrastructure.api.utils import get_db, current_user  # existing helpers

router = APIRouter(prefix="/api/v1/calibration", tags=["calibration"])


class DecisionIn(BaseModel):
    sample_id: uuid.UUID
    human_grade: str
    note: str = ""


class StatsOut(BaseModel):
    window_days: Optional[int]
    decided: int
    exact_match_extractor_rate: float
    exact_match_validator_rate: Optional[float]
    within_one_extractor_rate: float


@router.post("/decision", status_code=201)
def submit_decision(body: DecisionIn, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        record_human_verdict(
            db, sample_id=body.sample_id, human_grade=body.human_grade,
            decided_by=user.id, note=body.note,
        )
    except LookupError:
        raise HTTPException(404, "sample not found")
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    db.commit()
    return {"ok": True}


@router.get("/stats", response_model=StatsOut)
def get_stats(coverage: Optional[str] = None, window_days: Optional[int] = 30,
              db: Session = Depends(get_db), user=Depends(current_user)):
    s = compute_stats(db, coverage=coverage, window_days=window_days)
    return StatsOut(**s.__dict__)


@router.get("/pending")
def list_pending(coverage: Optional[str] = None, limit: int = 50,
                 db: Session = Depends(get_db), user=Depends(current_user)):
    from infrastructure.db.models import GradeCalibrationSample
    q = db.query(GradeCalibrationSample).filter_by(state="pending")
    if coverage:
        q = q.filter_by(coverage=coverage)
    rows = q.order_by(GradeCalibrationSample.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "submission_id": str(r.submission_id),
            "coverage": r.coverage,
            "signal_id": r.signal_id,
            "signal_weight": r.signal_weight,
            "extractor_grade": r.extractor_grade,
            "validator_grade": r.validator_grade,
            "sampling_reason": r.sampling_reason,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
```

## Steps

### 7.1 — Migration
**File**: `alembic/versions/025_grade_calibration.py`.
**Action**: Apply and round-trip.

### 7.2 — ORM
**File**: `infrastructure/db/models.py`.
**Action**: Add `GradeCalibrationSample` and `GradeCalibrationDecision`.

### 7.3 — Sampler
**File**: `signal_architecture/validation/sampler.py`.
**Action**: Implement deterministic stratified sampler.
**Test**: Same `mv_id` + same candidates → same target set. Buckets respected: every grade appearing in candidates with weight≥0.05 has at least one stratified pick.

### 7.4 — Store
**File**: `infrastructure/db/grade_calibration_store.py`.
**Action**: Implement `persist_samples`, `record_human_verdict`, `expire_old`, `stats`.
**Test**: Round-trip; double-recording rejected with 409; stats math correct.

### 7.5 — Workflow integration
**File**: `layers/risk/workflow.py`.
**Action**: After commit (Phase 5 stores) and validator (Phase 6):
1. Build `SamplingCandidate` list from the committed signals.
2. Run `select_targets`.
3. `persist_samples`.
4. If any sample's bucket has 30-day `exact_match_extractor_rate < 0.75`, emit `WeDriftAlert(category="grade_calibration_drift", coverage=...)`.

### 7.6 — API
**File**: `infrastructure/api/routes/grade_calibration.py`.
**Action**: Register the router in `infrastructure/api/main.py`. Re-use existing auth dependency.

### 7.7 — Tests
**Files**:
- `tests/unit/test_grade_calibration_sampler.py` — determinism, stratification, weight floor.
- `tests/unit/test_grade_calibration_store.py` — idempotency, expiration, stats.
- `tests/api/test_grade_calibration_endpoint.py` — happy-path POST, 404 on missing sample, 409 on double-decide.

## Test gates

```bash
alembic upgrade head
pytest tests/unit/test_grade_calibration_sampler.py tests/unit/test_grade_calibration_store.py -v
pytest tests/api/test_grade_calibration_endpoint.py -v
pytest tests/ -x -q

# End-to-end: seed bench, assert samples landed
python -m seed bench
psql -c "SELECT sampling_reason, COUNT(*) FROM grade_calibration_samples GROUP BY sampling_reason"
```

## Done when

- [ ] Sampler is deterministic for a given `mv_id`.
- [ ] Samples land idempotently — re-running the same cycle produces no duplicates.
- [ ] API endpoints functional, auth-gated, return correct error codes.
- [ ] Stats compute correct exact-match and within-one rates over rolling and lifetime windows.
- [ ] Drift alert fires when 30-day exact-match drops below 0.75 (tested with synthetic decisions).
- [ ] Full pytest green.

## Out of scope

- The underwriter UI for grade decisions. → Phase 14.
- Targeted re-extraction of signals where human disagrees with extractor. → Phase 13 (delta-aware re-extraction picks this up as a trigger).
- Auto-tuning `expected_grades` from calibration data. → V8.

## Invariants

1. A sample is recorded at most once per `(model_version_id, signal_id)`.
2. A decision is recorded at most once per sample.
3. `human_grade` is one of the five `EvidenceGrade` literals — validated at the API layer.
4. Pricing outputs unchanged. This phase is observation-only.
