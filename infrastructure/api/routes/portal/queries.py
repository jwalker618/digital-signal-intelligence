"""v8 Phase 6: /portal/queries -- broker inbox + reply alias.

  GET  /portal/queries                          -> BrokerQueriesResponse
  POST /portal/queries/{referral_code}/reply    -> delegates to Phase 5
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Broker,
    MessageDirection,
    Quote,
    Referral,
    ReferralMessage,
    ReferralStatus,
    Submission,
)

from .dependencies import get_user_record, require_portal_user
from .schemas import BrokerInfo, BrokerQueriesResponse, OpenQueryEntry

router = APIRouter()


@router.get("/queries", response_model=BrokerQueriesResponse)
async def broker_queries(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> BrokerQueriesResponse:
    """List open queries across the broker's book of clients."""
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
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

    # Pull referrals in AWAITING_BROKER for any submission this broker owns
    rows = await db.execute(
        select(Referral, Submission)
        .join(Quote, Referral.quote_id == Quote.id)
        .join(Submission, Quote.submission_id == Submission.id)
        .where(
            Submission.broker_id == user.broker_id,
            Referral.status == ReferralStatus.AWAITING_BROKER,
        )
        .order_by(Referral.updated_at.asc().nulls_first())
    )

    queries: list[OpenQueryEntry] = []
    for ref, sub in rows.all():
        # Last underwriter -> broker message
        msg_q = await db.execute(
            select(ReferralMessage)
            .where(
                ReferralMessage.referral_id == ref.id,
                ReferralMessage.direction == MessageDirection.UNDERWRITER_TO_BROKER.value,
            )
            .order_by(ReferralMessage.created_at.desc())
            .limit(1)
        )
        last_msg = msg_q.scalar_one_or_none()
        queries.append(
            OpenQueryEntry(
                referral_code=ref.referral_code,
                submission_code=sub.submission_code,
                entity_name=sub.entity_name,
                coverage=sub.coverage,
                request_signal_evidence=(
                    last_msg.request_signal_evidence if last_msg else None
                ),
                open_query_body=(last_msg.body if last_msg else None),
                opened_at=(last_msg.created_at if last_msg else ref.updated_at),
            )
        )

    return BrokerQueriesResponse(
        broker=BrokerInfo(id=str(broker.id), name=broker.name, slug=broker.slug),
        open_queries=queries,
    )


@router.post("/queries/{referral_code}/reply", status_code=status.HTTP_201_CREATED)
async def reply_alias(
    referral_code: str,
    payload: dict,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_REPLY)),
):
    """Convenience alias for /referrals/{code}/messages/reply (Phase 5).

    Same body shape, same behaviour -- routes through to the underlying
    handler so the portal frontend can call /portal/queries/{code}/reply.
    """
    from infrastructure.api.routes.referral_messages import (
        BrokerReplyRequest,
        broker_reply,
    )

    # Coerce into the Phase 5 request model
    try:
        request_model = BrokerReplyRequest(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reply payload: {exc}",
        )

    return await broker_reply(
        referral_code=referral_code,
        payload=request_model,
        db=db,
        ctx=ctx,
    )
