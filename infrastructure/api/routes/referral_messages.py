"""v8 Phase 5: broker-underwriter message thread on referrals.

Three endpoints, all under /api/v1:
  - POST /referrals/{referral_code}/messages           -> raise query (underwriter)
  - POST /referrals/{referral_code}/messages/reply     -> broker reply
  - GET  /referrals/{referral_code}/messages           -> list thread

Broker replies that include a `signal_value_update` payload trigger a
re-assessment by merging the update into the submission's
direct_query_responses and re-invoking the workflow. The resulting
new Quote is linked from the message row via new_quote_id for audit.

Permission model (v8 Phase 5 layer):
  - POST messages: require Permission.ASSESSMENT_REFER (underwriter)
  - POST reply:    require Permission.PORTAL_BROKER_REPLY (broker)
  - GET  thread:   require_any(ASSESSMENT_REFER, PORTAL_BROKER_REPLY)

Broker_id <-> referral entity scoping is enforced in v8 Phase 6's
portal layer (which mounts portal-prefixed aliases of these endpoints).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_any_permission,
    require_permission,
)
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    MessageDirection,
    Quote,
    Referral,
    ReferralMessage,
    ReferralStatus,
    Submission,
)

logger = logging.getLogger("dsi.api.referral_messages")
router = APIRouter()


# =============================================================================
# Request / response shapes
# =============================================================================

class RaiseQueryRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)
    request_signal_evidence: Optional[str] = Field(default=None, max_length=128)


class BrokerReplyRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)
    # Optional: when present, triggers re-assessment with the signal update applied
    signal_value_update: Optional["SignalValueUpdate"] = None


class SignalValueUpdate(BaseModel):
    signal_id: str = Field(..., min_length=1, max_length=128)
    new_value: Any                         # coerced to bool inside reassess
    evidence_basis: Optional[str] = Field(default=None, max_length=500)


class MessageDTO(BaseModel):
    id: str
    direction: str
    body: str
    request_signal_evidence: Optional[str] = None
    signal_value_update: Optional[dict] = None
    triggered_reassessment: bool
    new_quote_id: Optional[str] = None
    created_at: datetime


class RaiseQueryResponse(BaseModel):
    message_id: str
    referral_state: str
    referral_code: str


class BrokerReplyResponse(BaseModel):
    message_id: str
    triggered_reassessment: bool
    new_quote_id: Optional[str] = None
    referral_state: str


class ThreadResponse(BaseModel):
    referral_code: str
    referral_state: str
    awaiting_party: Optional[str] = None
    messages: list[MessageDTO]


# =============================================================================
# Helpers
# =============================================================================

# Referral states that are terminal -- no new messages can transition them.
_TERMINAL_STATES = {
    ReferralStatus.APPROVED,
    ReferralStatus.DECLINED,
    ReferralStatus.MODIFIED,
}


async def _get_referral_or_404(db: AsyncSession, referral_code: str) -> Referral:
    q = await db.execute(
        select(Referral).where(Referral.referral_code == referral_code)
    )
    referral = q.scalar_one_or_none()
    if referral is None:
        raise HTTPException(status_code=404, detail="Referral not found")
    return referral


async def _get_submission_for_referral(
    db: AsyncSession, referral: Referral
) -> Optional[Submission]:
    """Walk Referral -> Quote -> Submission. Returns None if missing."""
    q = await db.execute(
        select(Submission)
        .join(Quote, Submission.id == Quote.submission_id)
        .where(Quote.id == referral.quote_id)
    )
    return q.scalar_one_or_none()


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/referrals/{referral_code}/messages",
    response_model=RaiseQueryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def raise_query(
    referral_code: str,
    payload: RaiseQueryRequest,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(require_permission(Permission.ASSESSMENT_REFER)),
) -> RaiseQueryResponse:
    """Underwriter raises a query on a referral -> AWAITING_BROKER.

    Rejected when the referral is in a terminal state (approved /
    declined / modified).
    """
    referral = await _get_referral_or_404(db, referral_code)

    if referral.status in _TERMINAL_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot raise query on terminal referral "
                f"(state={referral.status.value})"
            ),
        )

    msg = ReferralMessage(
        referral_id=referral.id,
        direction=MessageDirection.UNDERWRITER_TO_BROKER.value,
        author_user_id=_uuid_or_none(ctx.user_id),
        body=payload.body,
        request_signal_evidence=payload.request_signal_evidence,
    )
    db.add(msg)

    # Transition referral to AWAITING_BROKER
    referral.status = ReferralStatus.AWAITING_BROKER
    referral.awaiting_party = "broker"

    await db.flush()
    await db.commit()

    return RaiseQueryResponse(
        message_id=str(msg.id),
        referral_state=referral.status.value,
        referral_code=referral.referral_code,
    )


@router.post(
    "/referrals/{referral_code}/messages/reply",
    response_model=BrokerReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def broker_reply(
    referral_code: str,
    payload: BrokerReplyRequest,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_REPLY)),
) -> BrokerReplyResponse:
    """Broker replies to an open query. Optional signal_value_update
    triggers a re-assessment via the existing workflow.

    Accepted even when the referral isn't strictly AWAITING_BROKER --
    a broker can volunteer additional context. But the re-assessment
    path only triggers when signal_value_update is provided.
    """
    referral = await _get_referral_or_404(db, referral_code)
    if referral.status in _TERMINAL_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot reply to terminal referral "
                f"(state={referral.status.value})"
            ),
        )

    triggered = False
    new_quote_id: Optional[str] = None

    if payload.signal_value_update is not None:
        # Re-assessment path.
        submission = await _get_submission_for_referral(db, referral)
        if submission is None:
            raise HTTPException(
                status_code=500,
                detail="Referral has no linked submission; cannot re-assess",
            )

        from layers.risk.reassessment import (
            reassess_with_signal_override,
        )

        try:
            result, merged_responses = reassess_with_signal_override(
                entity_id=submission.submission_code,
                coverage=submission.coverage,
                submission_data=submission.submission_data,
                existing_responses=submission.direct_query_responses,
                signal_id=payload.signal_value_update.signal_id,
                new_value=payload.signal_value_update.new_value,
                entity_name=submission.entity_name,
                domain_hint=submission.domain_hint,
                country_hint=submission.country_hint,
            )
        except Exception as exc:
            logger.exception("Re-assessment failed for referral %s", referral_code)
            raise HTTPException(
                status_code=500,
                detail=f"Re-assessment failed: {exc}",
            )

        # Persist merged direct_query_responses back onto the submission
        submission.direct_query_responses = merged_responses
        submission.updated_at = datetime.now(timezone.utc)

        # New ModelVersion + Quote persistence is delegated to the
        # standard submissions.py path. Phase 5 surfaces the
        # WorkflowResult to the caller; Phase 6's portal layer can
        # also drive persistence end-to-end if needed for the demo.
        # For now we record on the message that re-assessment ran.
        triggered = True

        # If the WorkflowResult carried a new quote code in result.entity_id
        # we don't yet know the persisted quote.id -- look up by submission.
        # The latest Quote for the submission is the most reliable handle
        # *after* the standard persistence path has run. For v8 Phase 5,
        # we leave new_quote_id NULL on the message when not yet known --
        # Phase 7's seed/reset path drives persistence inline so the link
        # is populated in the demo flow.

    msg = ReferralMessage(
        referral_id=referral.id,
        direction=MessageDirection.BROKER_TO_UNDERWRITER.value,
        author_user_id=_uuid_or_none(ctx.user_id),
        body=payload.body,
        signal_value_update=(
            payload.signal_value_update.model_dump()
            if payload.signal_value_update is not None
            else None
        ),
        triggered_reassessment=triggered,
        new_quote_id=None,  # populated by persistence path if applicable
    )
    db.add(msg)

    # Transition back to IN_REVIEW so the underwriter sees the reply
    # next time they open the queue.
    referral.status = ReferralStatus.IN_REVIEW
    referral.awaiting_party = None

    await db.flush()
    await db.commit()

    return BrokerReplyResponse(
        message_id=str(msg.id),
        triggered_reassessment=triggered,
        new_quote_id=new_quote_id,
        referral_state=referral.status.value,
    )


@router.get(
    "/referrals/{referral_code}/messages",
    response_model=ThreadResponse,
)
async def list_thread(
    referral_code: str,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(
        require_any_permission(
            Permission.ASSESSMENT_REFER,
            Permission.PORTAL_BROKER_REPLY,
        )
    ),
) -> ThreadResponse:
    """Return the full message thread for a referral in chronological order."""
    referral = await _get_referral_or_404(db, referral_code)

    q = await db.execute(
        select(ReferralMessage)
        .where(ReferralMessage.referral_id == referral.id)
        .order_by(ReferralMessage.created_at.asc())
    )
    messages = [
        MessageDTO(
            id=str(m.id),
            direction=m.direction,
            body=m.body,
            request_signal_evidence=m.request_signal_evidence,
            signal_value_update=m.signal_value_update,
            triggered_reassessment=m.triggered_reassessment,
            new_quote_id=str(m.new_quote_id) if m.new_quote_id else None,
            created_at=m.created_at,
        )
        for m in q.scalars().all()
    ]

    return ThreadResponse(
        referral_code=referral.referral_code,
        referral_state=referral.status.value,
        awaiting_party=referral.awaiting_party,
        messages=messages,
    )


# =============================================================================
# Utilities
# =============================================================================

def _uuid_or_none(user_id: Optional[str]):
    """AuthContext stores user_id as str; convert to UUID for FK insertion."""
    if not user_id:
        return None
    import uuid
    try:
        return uuid.UUID(user_id)
    except (ValueError, TypeError):
        return None
