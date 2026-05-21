# V7 Phase 8: Reproducibility Class

## Depends on
- Phase 2 (every produced signal carries a grade and sources).
- Phase 5 (`signal_history`).

## Blocks
- Phase 12 (mechanism memory wants only `stable` signals as priors).
- Phase 15 (frontend renders a reproducibility chip alongside grade).

## Scope

Introduce a separate categorical axis: **reproducibility class**. Distinct from confidence ("we got a value") and grade ("what kind of evidence"). Reproducibility answers: "if we re-pulled tomorrow, would the source agree with itself?"

Four classes:

- `stable` — multi-pull verified or source is a known-stable register (e.g. SEC EDGAR snapshot, classification society register).
- `flaky` — multi-pull shows occasional disagreement (≥50% but <90% agreement).
- `unstable` — frequent disagreement (<50% agreement) OR source returns different values per replica.
- `unknown` — single-pull, no reproducibility data yet.

Reproducibility is determined by the extractor and persisted on `SignalResult`. A new background job (cycle-end hook) selectively re-pulls a fraction of high-grade signals to build the stability record; results land in `signal_stability_observations`. Aggregation over observations classifies a `(source_id, signal_id)` pair.

This phase is the missing dispute-defence axis: a STRUCTURED_ATTESTED signal from a flaky source is epistemically weaker than the same grade from a stable register.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Reproducibility classes | `stable`, `flaky`, `unstable`, `unknown` (`Literal`) |
| D2 | Default | `unknown`. Becomes `stable` once ≥3 successful pulls within 30 days return equivalent values |
| D3 | Equivalence | Same `_values_equivalent` tolerance as Phase 3 — 5% numeric or exact categorical |
| D4 | Multi-pull triggering | Cycle-end hook. For 10% of high-grade (`structured_attested`+) signals per cycle, do an immediate second pull. For the remainder, schedule a deferred pull next cycle |
| D5 | Aggregation | `(source_id, signal_id, entity_id)` triple. Rolling 90-day window. Classify by agreement rate |
| D6 | Storage | New `signal_stability_observations` table. Lifetime: append-only. Aggregated view: `signal_stability_classification` materialised view refreshed daily |
| D7 | API | None in this phase. Frontend surface comes via Phase 15 |
| D8 | Pricing impact | None. Reproducibility is audit-only |
| D9 | Race-condition extractor flag | An extractor that flags itself as `race_sensitive=True` (e.g. live BGP, sentiment APIs) gets a relaxed 70% agreement threshold for `stable` instead of 90% (lifted from Clearwing `stability.py:43-44`) |
| D10 | Trust cap by reproducibility | A signal's effective grade for *commitment* purposes (Phase 5) is unchanged, but downstream Phase 12 (mechanism memory) and Phase 14 (disclosure packet) filter out `flaky`/`unstable` from "high-confidence audit material" |

## Files

### Create
- `alembic/versions/026_signal_stability.py`
- `signal_architecture/signals/stability.py` — observation recording + classification
- `infrastructure/db/stability_store.py`
- `tests/unit/test_signal_stability_classifier.py`
- `tests/unit/test_signal_stability_store.py`

### Modify
- `signal_architecture/signals/types.py` — add `reproducibility: Optional[Literal["stable","flaky","unstable","unknown"]] = None` to `SignalResult`
- `signal_architecture/signals/base.py` — add `RACE_SENSITIVE: bool = False` class attr to `BaseExtractor`
- `layers/risk/workflow.py` — cycle-end hook that schedules re-pulls
- `infrastructure/db/models.py` — `SignalStabilityObservation` ORM

## Migration `026`

```python
"""V7 Phase 8 — signal stability observations.

Revision ID: 026
Revises: 025
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "026"
down_revision = "025"


def upgrade():
    op.create_table(
        "signal_stability_observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("value_score", sa.Float, nullable=True),
        sa.Column("value_category", sa.String(128), nullable=True),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column("response_hash", sa.String(64), nullable=True),  # ties to signal_provenance
        sa.Column("race_sensitive", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_stability_obs_triple", "signal_stability_observations", ["source_id", "signal_id", "entity_id"])
    op.create_index("ix_stability_obs_observed", "signal_stability_observations", ["observed_at"])

    # Materialised view aggregates observations into a class per triple.
    op.execute("""
        CREATE MATERIALIZED VIEW signal_stability_classification AS
        WITH windowed AS (
            SELECT source_id, signal_id, entity_id, race_sensitive,
                   COUNT(*) AS n,
                   COUNT(DISTINCT value_hash) AS distinct_values
            FROM signal_stability_observations
            WHERE observed_at > now() - INTERVAL '90 days'
            GROUP BY source_id, signal_id, entity_id, race_sensitive
        )
        SELECT
            source_id, signal_id, entity_id, race_sensitive, n,
            CASE
                WHEN n < 3 THEN 'unknown'
                WHEN race_sensitive AND distinct_values::float / n <= 0.30 THEN 'stable'
                WHEN NOT race_sensitive AND distinct_values::float / n <= 0.10 THEN 'stable'
                WHEN distinct_values::float / n <= 0.50 THEN 'flaky'
                ELSE 'unstable'
            END AS class
        FROM windowed;
    """)
    op.execute("CREATE UNIQUE INDEX ix_stability_class_triple ON signal_stability_classification (source_id, signal_id, entity_id)")


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS signal_stability_classification")
    op.drop_index("ix_stability_obs_observed", table_name="signal_stability_observations")
    op.drop_index("ix_stability_obs_triple", table_name="signal_stability_observations")
    op.drop_table("signal_stability_observations")
```

## Stability module

`signal_architecture/signals/stability.py`:

```python
"""V7 Phase 8 — reproducibility classification.

Public API:
    canonical_value_hash(sig)
    record_observation(db, sig, *, source_id, entity_id, race_sensitive)
    lookup_class(db, source_id, signal_id, entity_id) -> ReproClass
    refresh_classification(db)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from signal_architecture.signals.types import SignalResult


ReproClass = Literal["stable", "flaky", "unstable", "unknown"]


def canonical_value_hash(sig: SignalResult) -> str:
    """Hash the asserted value (score | category) in a stable form.

    Score is quantised to 1 decimal so two pulls with negligible numeric drift
    hash identically. Category is exact match.
    """
    if sig.score is not None:
        payload = {"score": round(sig.score, 1)}
    elif sig.category is not None:
        payload = {"category": sig.category}
    else:
        payload = {"empty": True}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def record_observation(
    db: Session,
    sig: SignalResult,
    *,
    source_id: str,
    entity_id: str,
    race_sensitive: bool,
    response_hash: str | None = None,
) -> None:
    from infrastructure.db.models import SignalStabilityObservation
    db.add(SignalStabilityObservation(
        source_id=source_id,
        signal_id=sig.signal_id,
        entity_id=entity_id,
        value_score=sig.score,
        value_category=sig.category,
        value_hash=canonical_value_hash(sig),
        response_hash=response_hash,
        race_sensitive=race_sensitive,
    ))


def lookup_class(db: Session, *, source_id: str, signal_id: str, entity_id: str) -> ReproClass:
    row = db.execute(
        text("""
            SELECT class FROM signal_stability_classification
             WHERE source_id = :s AND signal_id = :sig AND entity_id = :e
        """),
        {"s": source_id, "sig": signal_id, "e": entity_id},
    ).first()
    if row is None:
        return "unknown"
    return row[0]


def refresh_classification(db: Session) -> None:
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY signal_stability_classification"))
```

## Cycle-end hook

`layers/risk/workflow.py` extension:

```python
import random

from signal_architecture.signals.stability import record_observation

def _record_initial_stability_observations(db, signals: list[SignalResult], entity_id: str):
    """First-pull observation. Single record per signal that has at least one
    EvidenceSource — multi-pull happens via re-extraction in subsequent cycles."""
    for sig in signals:
        if not sig.evidence_sources:
            continue
        primary = sig.evidence_sources[0]
        record_observation(
            db, sig,
            source_id=primary.source_id,
            entity_id=entity_id,
            race_sensitive=False,  # extractor sets True via class attr; default False
            response_hash=primary.response_hash,
        )


def _schedule_repulls(db, signals, entity_id: str, *, immediate_fraction: float = 0.10):
    """Pick 10% of structured_attested+ signals for an immediate second pull.

    Re-extract via the extractor registry, record_observation a second time.
    This builds n>=2 for stable classification within one cycle for that subset.
    """
    eligible = [s for s in signals if s.evidence_grade in ("structured_attested", "behaviourally_validated")]
    if not eligible:
        return
    k = max(1, int(round(immediate_fraction * len(eligible))))
    chosen = random.sample(eligible, k)
    for sig in chosen:
        # Re-run the inference function. NB: respects existing TTL cache —
        # set force_refresh=True so cache doesn't satisfy the second pull.
        # Implementation detail: the workflow knows how to re-invoke a single
        # inference function for one entity.
        re_sig = workflow_reinvoke_single(sig.signal_id, entity_id, force_refresh=True)
        if re_sig.evidence_sources:
            record_observation(
                db, re_sig,
                source_id=re_sig.evidence_sources[0].source_id,
                entity_id=entity_id,
                race_sensitive=False,
                response_hash=re_sig.evidence_sources[0].response_hash,
            )
```

## Steps

### 8.1 — Migration
**File**: `alembic/versions/026_signal_stability.py`.
**Action**: Apply. Round-trip up/down. The matview must rebuild on `down → up`.

### 8.2 — Type extension
**File**: `signal_architecture/signals/types.py`.
**Action**: Add `reproducibility` field to `SignalResult` with default `None`.

### 8.3 — Race-sensitive flag on extractor
**File**: `signal_architecture/signals/base.py`.
**Action**: Add `RACE_SENSITIVE: bool = False` on `BaseExtractor`. Set `True` on any sentiment/social-media/BGP/livestreaming extractors.

### 8.4 — Stability module
**File**: `signal_architecture/signals/stability.py` (create).
**Action**: Implement `canonical_value_hash`, `record_observation`, `lookup_class`, `refresh_classification`.
**Test**: `tests/unit/test_signal_stability_classifier.py` — agreement-ratio math, race-sensitive threshold, `unknown` when n<3.

### 8.5 — Workflow hook
**File**: `layers/risk/workflow.py`.
**Action**: Call `_record_initial_stability_observations` at cycle commit. Call `_schedule_repulls` over high-grade signals. Wire `workflow_reinvoke_single` if it does not already exist — small helper that resolves the inference function from the registry and runs it once.

### 8.6 — Hydrate `reproducibility` on read
**File**: a new helper in `signal_architecture/signals/stability.py`:
```python
def annotate_signals_with_reproducibility(db, signals, entity_id: str) -> None:
    """For each signal with sources, set `sig.reproducibility = lookup_class(...)`.

    Called by the scorer immediately before persistence so frontend
    sees the class on first render.
    """
    for sig in signals:
        if not sig.evidence_sources:
            sig.reproducibility = "unknown"
            continue
        primary = sig.evidence_sources[0]
        sig.reproducibility = lookup_class(
            db, source_id=primary.source_id,
            signal_id=sig.signal_id, entity_id=entity_id,
        )
```
Call from `workflow.py` after scoring + before commit (Phase 5 stores will then persist `reproducibility` — already part of `signal_history` because the column doesn't need to live on `model_version_signals`: it's a derivative of `signal_stability_classification`).

### 8.7 — Tests
**Files**:
- `tests/unit/test_signal_stability_classifier.py`
- `tests/unit/test_signal_stability_store.py`
- `tests/integration/test_stability_end_to_end.py` — seed two cycles for one entity, assert `lookup_class` transitions from `unknown` → `stable` after ≥3 agreeing pulls.

## Test gates

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head

pytest tests/unit/test_signal_stability_classifier.py \
        tests/unit/test_signal_stability_store.py \
        tests/integration/test_stability_end_to_end.py -v

pytest tests/ -x -q

# Sanity: after seed bench (multiple cycles), matview has rows
python -m seed bench
psql -c "REFRESH MATERIALIZED VIEW signal_stability_classification"
psql -c "SELECT class, COUNT(*) FROM signal_stability_classification GROUP BY class"
```

## Done when

- [ ] `SignalResult.reproducibility` populated by the workflow before commit.
- [ ] Cycle-end hook records initial observations for every graded signal.
- [ ] 10% of high-grade signals get an immediate second pull per cycle.
- [ ] `signal_stability_classification` matview returns correct class for synthetic agreement ratios.
- [ ] Race-sensitive extractors get the relaxed threshold.
- [ ] Pricing outputs unchanged.
- [ ] Full pytest green.

## Out of scope

- Hardening flaky signals via LLM retry (Clearwing's PoC hardening analog). → out of V7.
- Auto-demoting grades when reproducibility is `unstable`. → considered and rejected; reproducibility is a separate axis, not a grade modifier.
- API endpoint for reproducibility. → Phase 14.

## Invariants

1. Reproducibility class is a function of the observation history, never of the current cycle in isolation.
2. Race-sensitive extractors use the 70% threshold; everyone else uses 90%.
3. Multi-pull re-extraction respects per-source rate limits — the workflow's existing extractor caching machinery handles this via TTL.
4. No pricing impact.
