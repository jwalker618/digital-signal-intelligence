"""v8 Phase 8 polish: communications endpoints.

Two endpoints, both role-aware (BROKER + CLIENT):

  GET /portal/communications              -> CommunicationsListResponse
  GET /portal/communications/{referral}   -> CommunicationsThreadResponse

These supersede the more narrow /portal/queries inbox by exposing the
same data shape to clients too -- a client can see queries the
underwriter has raised against their own submissions, and the broker's
replies. Reply submission still flows through the Phase 5 endpoint
mounted at /api/v1/referrals/{code}/messages/reply (aliased from
/portal/queries/{code}/reply for broker convenience).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import AuthContext
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    MessageDirection,
    Quote,
    Referral,
    ReferralMessage,
    Submission,
    User,
)

from .dependencies import get_user_record, require_portal_user

router = APIRouter()


# ----------------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------------

class CommunicationItem(BaseModel):
    referral_code: str
    submission_code: str
    entity_name: str
    coverage: str
    policy_label: Optional[str] = None
    status: str
    awaiting_party: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_message_direction: Optional[str] = None
    last_message_excerpt: Optional[str] = None
    request_signal_evidence: Optional[str] = None
    is_open: bool


class CommunicationsListResponse(BaseModel):
    role: str
    items: list[CommunicationItem] = Field(default_factory=list)
    open_count: int = 0


class CommunicationThreadMessage(BaseModel):
    id: str
    direction: str
    body: str
    request_signal_evidence: Optional[str] = None
    signal_value_update: Optional[dict] = None
    triggered_reassessment: bool
    new_quote_id: Optional[str] = None
    created_at: datetime


class CommunicationsThreadResponse(BaseModel):
    referral_code: str
    submission_code: str
    entity_name: str
    coverage: str
    policy_label: Optional[str] = None
    status: str
    awaiting_party: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)
    messages: list[CommunicationThreadMessage] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _excerpt(text: Optional[str], max_len: int = 140) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


async def _scope_filter(
    db: AsyncSession, ctx: AuthContext, user: User,
):
    """Return a query filter that restricts referrals to the user's view.

    Broker: referrals on submissions where submission.broker_id == user.broker_id
    Client: referrals on submissions whose creator shares the user's tenant_id

    Returns a list of conditions for `.where(...)` use.
    """
    if ctx.role == "BROKER":
        if user.broker_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Broker identity not configured for this user",
            )
        return [Submission.broker_id == user.broker_id]

    # CLIENT
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not configured for this user",
        )
    # Find user ids in the same tenant so we can scope by submission.created_by
    creator_q = await db.execute(
        select(User.id).where(User.tenant_id == user.tenant_id)
    )
    creator_ids = [row[0] for row in creator_q.all()]
    if not creator_ids:
        return [Submission.id == uuid.UUID(int=0)]  # impossible match -> empty
    return [Submission.created_by.in_(creator_ids)]


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------

@router.get("/communications", response_model=CommunicationsListResponse)
async def list_communications(
    ctx: AuthContext = Depends(require_portal_user),
    db: AsyncSession = Depends(get_async_db),
    open_only: bool = False,
) -> CommunicationsListResponse:
    """List referrals visible to the current portal user.

    Pass ?open_only=true to restrict to referrals currently in
    AWAITING_BROKER or PENDING states.
    """
    user = await get_user_record(ctx, db)
    if user is None:
        raise HTTPException(403, "User record not found")

    conditions = await _scope_filter(db, ctx, user)

    q = await db.execute(
        select(Referral, Submission)
        .join(Quote, Referral.quote_id == Quote.id)
        .join(Submission, Quote.submission_id == Submission.id)
        .where(*conditions)
        .order_by(Referral.updated_at.desc().nulls_last())
    )

    items: list[CommunicationItem] = []
    open_count = 0
    for ref, sub in q.all():
        is_open = ref.awaiting_party is not None or ref.status.value in (
            "pending", "in_review", "awaiting_broker",
        )
        if open_only and not is_open:
            continue
        if is_open:
            open_count += 1

        # Last message in the thread, regardless of direction
        msg_q = await db.execute(
            select(ReferralMessage)
            .where(ReferralMessage.referral_id == ref.id)
            .order_by(ReferralMessage.created_at.desc())
            .limit(1)
        )
        last = msg_q.scalar_one_or_none()

        # Policy label lives in submission_data when seeded by demo-reset.
        policy_label = None
        if isinstance(sub.submission_data, dict):
            policy_label = sub.submission_data.get("policy_label")

        items.append(CommunicationItem(
            referral_code=ref.referral_code,
            submission_code=sub.submission_code,
            entity_name=sub.entity_name,
            coverage=sub.coverage,
            policy_label=policy_label,
            status=ref.status.value,
            awaiting_party=ref.awaiting_party,
            last_message_at=last.created_at if last else None,
            last_message_direction=last.direction if last else None,
            last_message_excerpt=_excerpt(last.body) if last else None,
            request_signal_evidence=last.request_signal_evidence if last and last.direction == MessageDirection.UNDERWRITER_TO_BROKER.value else None,
            is_open=is_open,
        ))

    return CommunicationsListResponse(
        role=ctx.role or "",
        items=items,
        open_count=open_count,
    )


@router.get(
    "/communications/{referral_code}",
    response_model=CommunicationsThreadResponse,
)
async def get_communication_thread(
    referral_code: str,
    ctx: AuthContext = Depends(require_portal_user),
    db: AsyncSession = Depends(get_async_db),
) -> CommunicationsThreadResponse:
    """Full thread for one referral, scope-checked."""
    user = await get_user_record(ctx, db)
    if user is None:
        raise HTTPException(403, "User record not found")

    conditions = await _scope_filter(db, ctx, user)

    q = await db.execute(
        select(Referral, Submission)
        .join(Quote, Referral.quote_id == Quote.id)
        .join(Submission, Quote.submission_id == Submission.id)
        .where(Referral.referral_code == referral_code, *conditions)
    )
    row = q.first()
    if row is None:
        raise HTTPException(404, "Referral not found or out of scope")

    ref, sub = row

    msgs_q = await db.execute(
        select(ReferralMessage)
        .where(ReferralMessage.referral_id == ref.id)
        .order_by(ReferralMessage.created_at.asc())
    )
    messages = [
        CommunicationThreadMessage(
            id=str(m.id),
            direction=m.direction,
            body=m.body,
            request_signal_evidence=m.request_signal_evidence,
            signal_value_update=m.signal_value_update,
            triggered_reassessment=m.triggered_reassessment,
            new_quote_id=str(m.new_quote_id) if m.new_quote_id else None,
            created_at=m.created_at,
        )
        for m in msgs_q.scalars().all()
    ]

    policy_label = None
    if isinstance(sub.submission_data, dict):
        policy_label = sub.submission_data.get("policy_label")

    reasons = list(ref.reasons) if isinstance(ref.reasons, list) else []

    return CommunicationsThreadResponse(
        referral_code=ref.referral_code,
        submission_code=sub.submission_code,
        entity_name=sub.entity_name,
        coverage=sub.coverage,
        policy_label=policy_label,
        status=ref.status.value,
        awaiting_party=ref.awaiting_party,
        reasons=reasons,
        messages=messages,
    )
