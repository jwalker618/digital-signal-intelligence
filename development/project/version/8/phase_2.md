# Version 8 Phase 2: Peer Cohort Engine

## Overview

Compute and persist a **percentile rank** for every scored submission against a defined peer cohort. Surface cohort summary statistics (mean score, distribution shape, top strengths/weaknesses) so the portal can later render peer-comparison views.

This is the engine that powers `/portal/peers` in Phase 8 and feeds the "your peers average 720, you scored 685" narrative in the demo.

## Rationale

v7 has no peer comparison anywhere — every score is presented in isolation. For a client to act on their signal score, they need to see it relative to comparable peers. For a broker (Marsh) to demonstrate value, they need to anchor their narrative in cohort context.

Per planning decision ("Real cohort from seed"), percentiles are computed from real scored entities in the database, not hand-picked demo cohorts. Phase 7 ensures cohort volume is sufficient (≥50 per cohort) for percentiles to be meaningful.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Cohort definition | (coverage_line, naics_section, revenue_band) | Triple key; balances specificity with cohort size |
| Percentile basis | Composite score across cohort members' latest quote | Single number per entity; recomputed when re-assessed |
| Persistence | New columns on `quotes` table (or model_version equivalent) | Computed at assessment time, served directly without recomputation |
| Cohort table | Yes — `cohort_membership` table | Allows direct cohort queries without scanning quotes |
| Revenue bands | Fixed buckets: <$10M, $10–50M, $50–250M, $250M–$1B, >$1B | Standard mid-market segmentation |
| NAICS section | 2-digit NAICS section (e.g. "51" Information) | Coarse enough to populate; specific enough to compare |
| Minimum cohort size | 10 entities for percentile to be reported; under that, return `null` | Honest — avoid bogus percentiles from thin cohorts |
| Where it runs | Post-scoring step in `layers/risk/workflow.py` | Reuses workflow; no parallel pipeline |
| Per-signal strengths/weaknesses | Top 3 above-cohort and bottom 3 below-cohort signals by absolute Z-score | Drives "you're strong in X, weak in Y" peer narrative |

## Current State

- `layers/risk/workflow.py` — runs the 14-step assessment. Scoring completes around step 5–6; pricing follows. No cohort step exists.
- `layers/risk/types.py` — `Quote` (or equivalent output dataclass) carries composite_score, tier, premium. No percentile field.
- `infrastructure/db/models.py` — `ModelVersionRecord` and/or `Quote` ORM stores assessment outputs. No percentile columns.
- `seed/synthetic.py` — generates entities per coverage; seed volume may be thin per cohort (Phase 7 will bulk up).
- No `naics_section` or `revenue_band` derived fields exist today — they need to be computed from existing entity attributes (NAICS code, annual revenue). Confirm exact field names during implementation.

## Target State

### Cohort identity

A cohort is identified by a triple:

```python
@dataclass(frozen=True)
class CohortKey:
    coverage_line: str        # "cyber", "casualty", ...
    naics_section: str        # 2-digit "51", "62", "31", ...
    revenue_band: str         # "<10M", "10-50M", "50-250M", "250M-1B", ">1B"
```

Encoded as a deterministic string `cohort_id` for storage: `"{coverage}:{naics}:{band}"`, e.g. `"cyber:51:50-250M"`.

### Revenue bands

```python
REVENUE_BANDS = [
    ("<10M",      0,             10_000_000),
    ("10-50M",    10_000_000,    50_000_000),
    ("50-250M",   50_000_000,    250_000_000),
    ("250M-1B",   250_000_000,   1_000_000_000),
    (">1B",       1_000_000_000, float("inf")),
]
```

Function `band_for(revenue: float) -> str` returns the band label. Boundary rule: lower-inclusive, upper-exclusive.

### Cohort membership table

```python
class CohortMembership(Base):
    __tablename__ = "cohort_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), nullable=False, index=True)
    cohort_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    coverage_line: Mapped[str] = mapped_column(String(32), nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("ix_cohort_lookup", "cohort_id", "composite_score"),
        UniqueConstraint("entity_id", "coverage_line", name="uq_entity_coverage_membership"),
    )
```

**One row per (entity, coverage_line)** — the latest cohort membership. Updated, not appended, on re-assessment.

### Quote columns

```python
class Quote(Base):  # extend existing
    # ... existing fields ...
    cohort_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    cohort_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentile_rank: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 to 100.0, or NULL if cohort too thin
    cohort_mean_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cohort_median_score: Mapped[float | None] = mapped_column(Float, nullable=True)
```

All nullable — assessments where the cohort is too thin (<10 members) leave these NULL but do not fail. Existing quotes without cohort data simply have NULL — no backfill required for legacy data.

### Cohort service

New package `layers/cohort/`:

```
layers/cohort/
    __init__.py
    service.py        # main API
    bands.py          # revenue band logic
    queries.py        # DB query helpers
```

**Public functions in `layers/cohort/service.py`:**

```python
def derive_cohort_key(entity: Entity, coverage_line: str) -> CohortKey:
    """Build cohort key for entity. Returns CohortKey or raises if entity lacks NAICS/revenue."""

def cohort_id_for(key: CohortKey) -> str:
    """'{coverage}:{naics}:{band}'"""

def upsert_membership(session, entity_id: int, cohort_id: str, coverage_line: str,
                      composite_score: float, quote_id: int) -> None:
    """Insert or update cohort membership for (entity, coverage_line)."""

def cohort_stats(session, cohort_id: str) -> CohortStats | None:
    """Return cohort size, mean, median, percentile thresholds. None if size < 10."""

def percentile_rank(session, cohort_id: str, score: float) -> float | None:
    """Return percentile (0-100) of score within cohort. None if cohort size < 10."""

def signal_strengths_weaknesses(session, entity_id: int, cohort_id: str,
                                coverage_line: str) -> SignalRanking:
    """Return top 3 strengths and bottom 3 weaknesses by Z-score vs cohort signal values."""
```

`CohortStats` and `SignalRanking` are Pydantic models (defined in `layers/cohort/service.py`).

### Workflow integration

In `layers/risk/workflow.py`:

**Insert a new step after the existing pricing step**, before the workflow returns:

```python
# ... after pricing completes and quote object has composite_score ...

if entity.naics_code and entity.annual_revenue:
    try:
        key = derive_cohort_key(entity, coverage_line)
        cid = cohort_id_for(key)
        upsert_membership(session, entity.id, cid, coverage_line,
                          quote.composite_score, quote.id)
        stats = cohort_stats(session, cid)
        if stats:
            quote.cohort_id = cid
            quote.cohort_size = stats.size
            quote.percentile_rank = percentile_rank(session, cid, quote.composite_score)
            quote.cohort_mean_score = stats.mean
            quote.cohort_median_score = stats.median
        else:
            quote.cohort_id = cid  # still record membership; just no stats yet
    except MissingCohortAttributesError:
        pass  # entity can't be cohorted; quote.cohort_id stays NULL
```

**Order matters**: cohort step runs **after** scoring and pricing produce final values, **before** the workflow's serialisation/return step.

### Migration

Alembic migration `latest + 2` (Phase 1 took `latest + 1`):

1. Create `cohort_membership` table with the schema above.
2. Add five columns to `quotes`: `cohort_id`, `cohort_size`, `percentile_rank`, `cohort_mean_score`, `cohort_median_score`. All nullable.
3. Backfill: leave NULL. Cohort populates as re-assessments run.

Down migration drops the table and columns.

### Percentile computation algorithm

```python
def percentile_rank(session, cohort_id: str, score: float) -> float | None:
    rows = session.query(CohortMembership.composite_score)\
        .filter(CohortMembership.cohort_id == cohort_id)\
        .all()
    if len(rows) < MIN_COHORT_SIZE:  # 10
        return None
    scores = sorted(r.composite_score for r in rows)
    # number of cohort members with strictly lower score
    below = sum(1 for s in scores if s < score)
    # half credit for ties (inclusive convention)
    equal = sum(1 for s in scores if s == score)
    rank = (below + 0.5 * equal) / len(scores)
    return round(rank * 100.0, 1)
```

Returns 0.0 to 100.0. Tie convention: half-credit.

### Signal strengths/weaknesses

For each signal in the entity's most recent signal_results for this coverage:

1. Look up cohort distribution of that signal value (using `cohort_membership` join with signal results — query helper in `layers/cohort/queries.py`).
2. Compute Z-score: `(entity_value - cohort_mean) / cohort_stddev`. Skip if stddev is 0 or undefined.
3. Sort signals by Z-score.
4. Return top 3 (highest positive Z, "strengths") and bottom 3 (lowest negative Z, "weaknesses").

Returned shape:

```python
class SignalRankEntry(BaseModel):
    signal_id: str
    entity_value: float
    cohort_mean: float
    z_score: float

class SignalRanking(BaseModel):
    strengths: list[SignalRankEntry]  # length ≤ 3
    weaknesses: list[SignalRankEntry]  # length ≤ 3
```

If cohort too thin or signal data missing, return empty lists. No errors.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Exact location of `Quote` ORM model (`infrastructure/db/models.py` or `infrastructure/models/`).
2. Where signal values per entity are stored after assessment (likely `signal_results` table or similar).
3. Exact location of the workflow function in `layers/risk/workflow.py` (function name, return point).
4. NAICS code field name on `Entity`. Revenue field name.
5. Latest Alembic migration number after Phase 1.

### Step 2: Migration

Write and test `latest + 2` migration with the schema additions above. Apply, rollback, re-apply on local DB.

### Step 3: `layers/cohort/` package

Create the package with `bands.py`, `service.py`, `queries.py`. Implement the public functions. No workflow integration yet.

### Step 4: Tests for `layers/cohort/`

- `tests/cohort/test_bands.py`: every band boundary, edge values.
- `tests/cohort/test_service.py`:
  - `derive_cohort_key` produces stable keys.
  - `cohort_id_for` round-trips.
  - `upsert_membership` inserts then updates (does not duplicate).
  - `cohort_stats` returns None for cohorts < 10, returns stats for ≥ 10.
  - `percentile_rank` correctness: known distributions, tie cases, edge cases (lowest, highest, missing).
  - `signal_strengths_weaknesses` returns ≤3 each, handles thin cohorts and missing signals.

### Step 5: Workflow integration

Add the cohort step to `layers/risk/workflow.py` per the **Workflow integration** section. Single insertion point. Wrap in try/except for `MissingCohortAttributesError` so non-cohortable entities (no NAICS or revenue) still complete successfully.

### Step 6: End-to-end test

`tests/api/test_cohort_e2e.py` (or extend existing E2E):
- Seed 15 entities into the same cohort with varied scores.
- Run assessment on a 16th entity.
- Assert `quote.cohort_id` matches expected, `quote.cohort_size == 16`, `quote.percentile_rank` in (0, 100).
- Run assessment on an entity in a fresh cohort (size < 10).
- Assert `quote.percentile_rank is None`, `quote.cohort_size < 10`, but `quote.cohort_id` is still set.

## Constraints & Principles

1. **No endpoint exposure in Phase 2.** The cohort service is consumed by Phase 6's portal API. Do not mount endpoints here.
2. **Cohort is recomputed-on-write, not precomputed.** A cohort's stats reflect membership at the time of query; no caching, no scheduled jobs.
3. **Honest under thin data.** Cohort < 10 → percentile is `null`, not "100%" or "50%" or a guess. UI handles null by rendering "not enough peers yet."
4. **Single source of truth.** Once cohort step runs, `quote.percentile_rank` is authoritative. The portal never recomputes percentile at read time.
5. **Performance.** Cohort percentile query is `O(cohort_size)` on the index. Acceptable up to ~10k members per cohort; if cohorts grow past that, revisit with a histogram approach (v8.1+).
6. **No retroactive backfill.** Existing quotes pre-v8 stay NULL on the new columns. Only newly-assessed entities populate them. Phase 7's demo reset will trigger fresh assessments to populate the demo cohort.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Existing entities lack NAICS or revenue, can't be cohorted | Try/except in workflow leaves cohort fields NULL. Quote still completes. |
| Cohort cardinality explosion (too many small cohorts) | NAICS section (2-digit) chosen specifically to keep cohort counts manageable. Revenue bands are coarse. |
| Z-score is undefined for cohorts with zero variance on a signal | Skip that signal in strengths/weaknesses. Documented in service.py. |
| Percentile changes unpredictably as cohort grows | Acceptable — that's how percentiles work. UI can show "as of N peers" to make it explicit. |
| Re-assessment of one entity changes percentiles of others | True but they're not stored elsewhere — percentile is computed fresh per assessment. No staleness in the system, just in the UI render. |
| Workflow now does an extra DB write per assessment | One `INSERT … ON CONFLICT UPDATE` and ~3 SELECTs. Negligible cost. |

## Dependencies

- **Phase 1 complete.** `Broker` and roles exist (Phase 2 doesn't use them directly, but the data model must be stable).
- Existing scoring and pricing produce a populated `Quote.composite_score`.
- Entities have `naics_code` and `annual_revenue` populated where cohorting is desired. For demo, Phase 7 ensures this.

## Success Criteria

1. `layers/cohort/` package exists with `bands.py`, `service.py`, `queries.py`.
2. All public service functions implemented and tested per **Step 4**.
3. Migration `latest + 2` applies and rolls back cleanly.
4. `cohort_membership` table populated by every new assessment where entity has NAICS + revenue.
5. `quotes.cohort_id`, `cohort_size`, `percentile_rank`, `cohort_mean_score`, `cohort_median_score` populated on every new assessment with cohortable entity.
6. Quotes with cohort size < 10 have `cohort_id` set but `percentile_rank` NULL.
7. End-to-end test passes per **Step 6**.
8. Full `pytest tests/ -v` green.
9. No endpoints added. No frontend touched. No seed touched.

## Out of Scope (Phase 2)

- API endpoints exposing percentile data — Phase 6.
- Frontend peer comparison page — Phase 8.
- Bulking up cohort volume — Phase 7.
- Cohort drift monitoring or alerts — v8.1+.
- Multiple cohort definitions (e.g. industry-specific) — single definition only.
- Historical percentile tracking — current value only.
