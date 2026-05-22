"""v8 Phase 2: async DB helpers for cohort membership and percentile lookup.

These functions are the impure side of the cohort engine: they touch
the database. All math lives in service.py. Callers compose:

    key = derive_cohort_key(submission_data, coverage)  # service.py
    cohort_id = cohort_id_for(key)                       # service.py
    await upsert_membership(session, ...)                # this module
    stats = await get_cohort_stats(session, cohort_id)   # this module
    percentile = await get_percentile_rank(session, cohort_id, score)

Call from infrastructure/api/routes/submissions.py at the point where
the new ModelVersionRecord has just been persisted -- it has an id, a
final_composite_score, and access to the original Submission via FK.
"""
from __future__ import annotations

import statistics
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import CohortMembership, ModelVersionRecord

from .service import (
    MIN_COHORT_SIZE,
    CohortStats,
    cohort_stats_from_scores,
    percentile_from_scores,
)


async def upsert_membership(
    session: AsyncSession,
    *,
    entity_key: str,
    coverage: str,
    cohort_id: str,
    composite_score: float,
    naics_section: str,
    revenue_band: str,
    model_version_id: uuid.UUID,
) -> None:
    """Insert-or-update the cohort_membership row for (entity_key, coverage).

    Uses PostgreSQL's ON CONFLICT (entity_key, coverage) so re-assessment
    of an entity updates the existing row rather than producing a new
    one. last_assessed_at and model_version_id refresh on every upsert.
    """
    stmt = pg_insert(CohortMembership).values(
        entity_key=entity_key,
        coverage=coverage,
        cohort_id=cohort_id,
        composite_score=composite_score,
        naics_section=naics_section,
        revenue_band=revenue_band,
        model_version_id=model_version_id,
        last_assessed_at=datetime.utcnow(),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["entity_key", "coverage"],
        set_={
            "cohort_id": stmt.excluded.cohort_id,
            "composite_score": stmt.excluded.composite_score,
            "naics_section": stmt.excluded.naics_section,
            "revenue_band": stmt.excluded.revenue_band,
            "model_version_id": stmt.excluded.model_version_id,
            "last_assessed_at": stmt.excluded.last_assessed_at,
        },
    )
    await session.execute(stmt)


async def fetch_cohort_scores(
    session: AsyncSession, cohort_id: str
) -> list[float]:
    """Return all current composite scores in a cohort."""
    result = await session.execute(
        select(CohortMembership.composite_score).where(
            CohortMembership.cohort_id == cohort_id
        )
    )
    return [row[0] for row in result.all()]


async def get_cohort_stats(
    session: AsyncSession, cohort_id: str
) -> Optional[CohortStats]:
    """Return cohort summary stats, or None if cohort is too thin."""
    scores = await fetch_cohort_scores(session, cohort_id)
    return cohort_stats_from_scores(cohort_id, scores)


async def get_percentile_rank(
    session: AsyncSession, cohort_id: str, score: float
) -> Optional[float]:
    """Return the entity's percentile rank within its cohort, or None if thin.

    Uses the same scoring snapshot as get_cohort_stats. Half-credit tie
    convention. See service.percentile_from_scores for details.
    """
    scores = await fetch_cohort_scores(session, cohort_id)
    return percentile_from_scores(scores, score)


async def assign_cohort_to_model_version(
    session: AsyncSession,
    *,
    model_version: ModelVersionRecord,
    entity_key: str,
    cohort_id: str,
    composite_score: float,
    naics_section: str,
    revenue_band: str,
    coverage: str,
) -> None:
    """Top-level entry point used by the persistence layer.

    Upserts membership, fetches fresh cohort stats, populates the
    peer_cohort_* fields on the given ModelVersionRecord. The caller
    (submissions.py) is responsible for committing the session.

    All five peer_cohort_* fields are populated:
      - peer_cohort_id always set
      - peer_cohort_size always set (may be 1 if this entity is alone)
      - peer_percentile_rank set only when cohort meets MIN_COHORT_SIZE;
        otherwise NULL
      - peer_cohort_mean_score and peer_cohort_median_score follow the
        same MIN_COHORT_SIZE rule
    """
    await upsert_membership(
        session,
        entity_key=entity_key,
        coverage=coverage,
        cohort_id=cohort_id,
        composite_score=composite_score,
        naics_section=naics_section,
        revenue_band=revenue_band,
        model_version_id=model_version.id,
    )

    # Re-read the cohort _after_ inserting this entity so the stats
    # include the entity itself. Matches the audit-trail principle:
    # the percentile reported is "of this entity within the cohort
    # snapshot at this moment in time", inclusive.
    scores = await fetch_cohort_scores(session, cohort_id)
    model_version.peer_cohort_id = cohort_id
    model_version.peer_cohort_size = len(scores)

    stats = cohort_stats_from_scores(cohort_id, scores)
    if stats is not None:
        model_version.peer_cohort_mean_score = stats.mean
        model_version.peer_cohort_median_score = stats.median
        model_version.peer_percentile_rank = percentile_from_scores(
            scores, composite_score
        )
    # else: cohort below threshold; mean/median/percentile stay NULL.
