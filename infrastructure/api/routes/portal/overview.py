"""v8 Phase 6: /portal/overview -- role-aware landing data.

BROKER view: book of clients (one row per submission with current
quote / referral state).

CLIENT view: own entity + active coverages.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import AuthContext
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Broker,
    ModelVersionRecord,
    Quote,
    Referral,
    ReferralStatus,
    Submission,
    User,
)

from .dependencies import get_user_record, require_portal_user
from .schemas import (
    BrokerInfo,
    BrokerOverviewResponse,
    ClientBookEntry,
    ClientCoverageEntry,
    ClientOverviewResponse,
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
    coverages = [await _build_coverage_entry(s, db) for s in submissions]
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


async def _build_coverage_entry(
    submission: Submission, db: AsyncSession,
) -> ClientCoverageEntry:
    mv = await _latest_mv_for_submission(submission, db)
    quote = await _latest_quote_for_submission(submission, db)
    referral = await _open_referral_for_submission(submission, db)
    return ClientCoverageEntry(
        submission_code=submission.submission_code,
        coverage=submission.coverage,
        composite_score=(mv.final_composite_score if mv else None),
        tier=(mv.final_tier if mv else None),
        peer_percentile_rank=(mv.peer_percentile_rank if mv else None),
        recommended_premium=(quote.recommended_premium if quote else None),
        referral_state=(referral.status.value if referral else None),
        updated_at=submission.updated_at,
    )
