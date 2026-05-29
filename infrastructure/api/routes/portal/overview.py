"""v8 Phase 6: /portal/overview -- role-aware landing data.

BROKER view: book of clients (one row per submission with current
quote / referral state).

CLIENT view: own entity + active coverages.
"""
from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import AuthContext
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Broker,
    CommercialTermsRecord,
    LossEvent,
    ModelVersionRecord,
    Quote,
    Referral,
    ReferralStatus,
    RiskTermsRecord,
    Submission,
    User,
)
from layers.cohort.queries import fetch_cohort_scores

from .dependencies import get_user_record, require_portal_user
from .schemas import (
    BrokerInfo,
    BrokerOverviewResponse,
    ClientBookEntry,
    ClientCoverageEntry,
    ClientOverviewResponse,
    ScoreHistoryPoint,
)

router = APIRouter()


@router.get("/overview")
async def overview(
    ctx: AuthContext = Depends(require_portal_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Return role-aware overview payload.

    Response shape varies by role:
      BROKER -> BrokerOverviewResponse
      CLIENT -> ClientOverviewResponse
    """
    user = await get_user_record(ctx, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User record not found",
        )

    if ctx.role == "BROKER":
        return await _broker_overview(user, db)
    return await _client_overview(user, db)


async def _broker_overview(user: User, db: AsyncSession) -> BrokerOverviewResponse:
    if user.broker_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Broker identity not configured for this user",
        )

    broker_q = await db.execute(select(Broker).where(Broker.id == user.broker_id))
    broker = broker_q.scalar_one_or_none()
    if broker is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Linked broker not found",
        )

    submissions_q = await db.execute(
        select(Submission).where(Submission.broker_id == user.broker_id)
    )
    submissions = list(submissions_q.scalars().all())

    clients = [await _build_book_entry(s, db) for s in submissions]
    clients.sort(key=lambda c: (c.updated_at is None, c.updated_at), reverse=True)

    open_queries_q = await db.execute(
        select(func.count(Referral.id))
        .join(Quote, Referral.quote_id == Quote.id)
        .join(Submission, Quote.submission_id == Submission.id)
        .where(
            Submission.broker_id == user.broker_id,
            Referral.status == ReferralStatus.AWAITING_BROKER,
        )
    )
    open_queries_count = open_queries_q.scalar() or 0

    return BrokerOverviewResponse(
        broker=BrokerInfo(id=str(broker.id), name=broker.name, slug=broker.slug),
        clients=clients,
        open_queries_count=open_queries_count,
    )


async def _client_overview(user: User, db: AsyncSession) -> ClientOverviewResponse:
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not configured for this user",
        )

    submissions_q = await db.execute(
        select(Submission).where(Submission.created_by == user.id)
    )
    submissions = list(submissions_q.scalars().all())

    entity_name = submissions[0].entity_name if submissions else (user.full_name or "")
    broker_info = await _broker_info_for_submission(
        submissions[0] if submissions else None, db,
    )
    coverages = [
        await _build_coverage_entry(s, user.tenant_id, db) for s in submissions
    ]
    coverages.sort(key=lambda c: (c.updated_at is None, c.updated_at), reverse=True)

    return ClientOverviewResponse(
        entity_name=entity_name,
        broker=broker_info,
        active_coverages=coverages,
    )


async def _broker_info_for_submission(
    submission: Optional[Submission], db: AsyncSession,
) -> Optional[BrokerInfo]:
    if submission is None or submission.broker_id is None:
        return None
    q = await db.execute(select(Broker).where(Broker.id == submission.broker_id))
    b = q.scalar_one_or_none()
    if b is None:
        return None
    return BrokerInfo(id=str(b.id), name=b.name, slug=b.slug)


async def _latest_mv_for_submission(
    submission: Submission, db: AsyncSession,
) -> Optional[ModelVersionRecord]:
    q = await db.execute(
        select(ModelVersionRecord).where(
            ModelVersionRecord.submission_id == submission.id,
            ModelVersionRecord.is_latest == True,  # noqa: E712
        )
    )
    return q.scalar_one_or_none()


async def _latest_quote_for_submission(
    submission: Submission, db: AsyncSession,
) -> Optional[Quote]:
    q = await db.execute(
        select(Quote).where(Quote.submission_id == submission.id).order_by(
            Quote.created_at.desc()
        ).limit(1)
    )
    return q.scalar_one_or_none()


async def _open_referral_for_submission(
    submission: Submission, db: AsyncSession,
) -> Optional[Referral]:
    q = await db.execute(
        select(Referral)
        .join(Quote, Referral.quote_id == Quote.id)
        .where(Quote.submission_id == submission.id)
        .order_by(Referral.created_at.desc())
        .limit(1)
    )
    return q.scalar_one_or_none()


async def _build_book_entry(
    submission: Submission, db: AsyncSession,
) -> ClientBookEntry:
    mv = await _latest_mv_for_submission(submission, db)
    quote = await _latest_quote_for_submission(submission, db)
    referral = await _open_referral_for_submission(submission, db)
    return ClientBookEntry(
        submission_code=submission.submission_code,
        entity_name=submission.entity_name,
        coverage=submission.coverage,
        status=submission.status.value if submission.status else "unknown",
        composite_score=(mv.final_composite_score if mv else None),
        tier=(mv.final_tier if mv else None),
        peer_percentile_rank=(mv.peer_percentile_rank if mv else None),
        recommended_premium=(quote.recommended_premium if quote else None),
        referral_state=(referral.status.value if referral else None),
        awaiting_party=(referral.awaiting_party if referral else None),
        updated_at=submission.updated_at,
    )


# How many model_version rows to surface for the client overview
# sparkline. Bounded so a long-lived submission doesn't bloat the
# payload; the page only renders a small spark trail.
_SCORE_HISTORY_LIMIT = 8


def _quarter_start(d: datetime) -> datetime:
    """Floor `d` to the start of its calendar quarter (UTC)."""
    q_first_month = ((d.month - 1) // 3) * 3 + 1
    return datetime(d.year, q_first_month, 1, tzinfo=timezone.utc)


def _quarter_back(start: datetime, n: int) -> datetime:
    """Return the start of the quarter that is `n` quarters before `start`."""
    total_q = start.year * 4 + (start.month - 1) // 3 - n
    year, q = divmod(total_q, 4)
    return datetime(year, q * 3 + 1, 1, tzinfo=timezone.utc)


async def _loss_event_quarters_for_coverage(
    entity_name: str,
    coverage: str,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[list[float]]:
    """Aggregate incurred loss per quarter for an entity's coverage, last 12 Q.

    Returns 12 floats oldest -> newest, normalised so max = 1.0. The
    strip is purely a visual density indicator (no absolute scale), so
    normalising lets the UI render bars consistently regardless of book
    size. Returns None when the entity has no loss events at all — the
    frontend falls back to its designed placeholder in that case.
    """
    now = datetime.now(timezone.utc)
    current_q_start = _quarter_start(now)
    window_start = _quarter_back(current_q_start, 11)  # 12 quarters inclusive

    q = await db.execute(
        select(LossEvent.loss_date, LossEvent.incurred_amount).where(
            LossEvent.tenant_id == tenant_id,
            LossEvent.entity_name == entity_name,
            LossEvent.coverage == coverage,
            LossEvent.loss_date >= window_start,
        )
    )
    rows = list(q.all())
    if not rows:
        return None

    buckets = [0.0] * 12
    for loss_date, incurred in rows:
        if loss_date is None or incurred is None:
            continue
        # Buckets are ordered oldest -> newest. Index = quarters since window_start.
        delta_q = (loss_date.year - window_start.year) * 4 + (
            (loss_date.month - 1) // 3 - (window_start.month - 1) // 3
        )
        if 0 <= delta_q < 12:
            buckets[delta_q] += float(incurred)

    peak = max(buckets)
    if peak <= 0:
        # Events existed but fell outside the window -- nothing to plot.
        return None
    return [round(v / peak, 4) for v in buckets]


async def _build_coverage_entry(
    submission: Submission,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> ClientCoverageEntry:
    mv = await _latest_mv_for_submission(submission, db)
    quote = await _latest_quote_for_submission(submission, db)
    referral = await _open_referral_for_submission(submission, db)

    # Phase F.2: risk + commercial terms for the Coverages policy facts.
    risk = None
    commercial = None
    if mv is not None:
        r_q = await db.execute(
            select(RiskTermsRecord).where(RiskTermsRecord.model_version_id == mv.id)
        )
        risk = r_q.scalar_one_or_none()
        c_q = await db.execute(
            select(CommercialTermsRecord).where(
                CommercialTermsRecord.model_version_id == mv.id
            )
        )
        commercial = c_q.scalar_one_or_none()

    # Phase B1: fetch a short history of MV rows so we can derive
    # previous score, the score-history sparkline, and the prior
    # exposure value (for YoY). One extra query per coverage; for the
    # small N of coverages a client has this is fine.
    history_q = await db.execute(
        select(ModelVersionRecord)
        .where(ModelVersionRecord.submission_id == submission.id)
        .order_by(ModelVersionRecord.version_number.desc())
        .limit(_SCORE_HISTORY_LIMIT)
    )
    history_desc = list(history_q.scalars().all())

    previous_composite_score: Optional[float] = None
    exposure_value_prior: Optional[float] = None
    score_history: Optional[list[ScoreHistoryPoint]] = None
    if len(history_desc) >= 2:
        prior = history_desc[1]
        previous_composite_score = prior.final_composite_score
        exposure_value_prior = prior.exposure_value
    if history_desc:
        # Reverse to oldest -> newest for the sparkline. Drop rows with no
        # composite score (very early scoring failures); the sparkline
        # would skip them anyway.
        ordered = list(reversed(history_desc))
        score_history = [
            ScoreHistoryPoint(
                version_number=row.version_number,
                composite_score=row.final_composite_score,
                created_at=row.created_at,
            )
            for row in ordered
            if row.final_composite_score is not None and row.created_at is not None
        ] or None

    # Cohort range stats: pull the cohort score list and derive min /
    # max / p90 inline. cohort_stats_from_scores already exposes
    # median/p25/p75 elsewhere, but the overview only needs the
    # range + top decile and we already have the median on the MV row.
    peer_cohort_top_decile: Optional[float] = None
    peer_cohort_min: Optional[float] = None
    peer_cohort_max: Optional[float] = None
    if mv is not None and mv.peer_cohort_id:
        scores = await fetch_cohort_scores(db, mv.peer_cohort_id)
        if scores:
            peer_cohort_min = float(min(scores))
            peer_cohort_max = float(max(scores))
            # quantiles(n=10) splits into deciles; the last cut is p90.
            # statistics.quantiles requires at least 2 points.
            if len(scores) >= 2:
                try:
                    peer_cohort_top_decile = float(
                        statistics.quantiles(scores, n=10)[-1]
                    )
                except statistics.StatisticsError:
                    peer_cohort_top_decile = None

    return ClientCoverageEntry(
        submission_code=submission.submission_code,
        coverage=submission.coverage,
        composite_score=(mv.final_composite_score if mv else None),
        tier=(mv.final_tier if mv else None),
        peer_percentile_rank=(mv.peer_percentile_rank if mv else None),
        recommended_premium=(quote.recommended_premium if quote else None),
        referral_state=(referral.status.value if referral else None),
        updated_at=submission.updated_at,
        peer_cohort_median_score=(mv.peer_cohort_median_score if mv else None),
        peer_cohort_size=(mv.peer_cohort_size if mv else None),
        peer_cohort_top_decile=peer_cohort_top_decile,
        peer_cohort_min=peer_cohort_min,
        peer_cohort_max=peer_cohort_max,
        previous_composite_score=previous_composite_score,
        score_history=score_history,
        exposure_value=(mv.exposure_value if mv else None),
        exposure_band_label=(mv.exposure_band_label if mv else None),
        exposure_size_score=(mv.exposure_size_score if mv else None),
        exposure_value_prior=exposure_value_prior,
        # Phase B2: loss-outlook fields straight off the latest MV row.
        loss_propensity_band=(mv.loss_propensity_band if mv else None),
        loss_trend_direction=(mv.loss_trend_direction if mv else None),
        loss_frequency_velocity=(mv.loss_frequency_velocity if mv else None),
        loss_severity_velocity=(mv.loss_severity_velocity if mv else None),
        loss_event_quarters=await _loss_event_quarters_for_coverage(
            submission.entity_name, submission.coverage, tenant_id, db,
        ),
        # Phase F.2: policy facts.
        limit=(mv.recommended_limit if mv else None),
        deductible=(risk.deductible_amount if risk else None),
        aggregate_limit=(risk.aggregate_limit if risk else None),
        expires_at=(commercial.earned_end if commercial else None),
    )
