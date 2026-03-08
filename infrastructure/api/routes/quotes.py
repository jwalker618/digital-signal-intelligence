"""
DSI Quote Endpoints (Phase 11) - Database Backed

Endpoints for retrieving and managing quotes.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote, 
    QuoteStatus,
    Referral,
    ReferralStatus
)

from ..utils import generate_id

from ..types import (
    QuoteRecord,
)

from infrastructure.api.routes.referrals import updateStatus_referral

logger = logging.getLogger("dsi.api.quotes")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/quotes/{quote_code}", response_model=QuoteRecord)
async def get_quote(
    quote_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> QuoteRecord:
    """Get quote details by code."""
    query = select(Quote).where(Quote.quote_code == quote_code)
    
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Quote not found")

    return record

@router.post("/quotes/{quote_code}/update-status")
async def updateStatus_quote(
    quote_code: str,
    status: QuoteStatus,
    db: AsyncSession = Depends(get_async_db),
    commit: bool = True
) -> Dict[str, Any]:
    """Update the status of a quote."""
    query = select(Quote).where(Quote.quote_code == quote_code)
    q = (await db.execute(query)).scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    if q.status != QuoteStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Quote cannot be updated in current status: {q.status.value}",
        )

    # Expiration safety check
    if status == QuoteStatus.BOUND and q.valid_until and q.valid_until < datetime.now(timezone.utc):
        q.status = QuoteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Quote has expired")

    q.status = QuoteStatus(status.value)
    
    if status == QuoteStatus.BOUND:
        q.bound_at = datetime.now(timezone.utc)
        q.policy_number = generate_id("pol")

    if commit:
        await db.commit()

    return {
        "status": "success",
        "message": f"Quote status: {q.status.value}",
        "quote_code": q.quote_code,
        "updated_at": q.updated_at,
        "policy_number": getattr(q, 'policy_number', None),
        "bound_at": getattr(q, 'bound_at', None),
    }

@router.post("/quotes/{quote_code}/resolve")
async def resolve_workflow(
    quote_code: str,
    quote_action: QuoteStatus,
    referral_action: Optional[ReferralStatus],
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Simultaneously resolve an attached referral AND update the quote 
    by orchestrating the standalone endpoints in a single transaction.
    """
    ref_response = None
    
    # 1. Execute Referral Action (NO COMMIT)
    if referral_action:
        ref_response = await updateStatus_referral(
            quote_code=quote_code, 
            status=referral_action, 
            db=db, 
            commit=False
        )

    # 2. Composite Business Rule: Cannot bind if referral isn't approved
    if quote_action == QuoteStatus.BOUND:
        qry_referral = select(Referral).join(Quote, Referral.quote_id == Quote.id).where(Quote.quote_code == quote_code)
        qR = (await db.execute(qry_referral)).scalar_one_or_none()
        
        # We check qR.status here. Because they share the `db` session, it sees the update from step 1!
        if qR and qR.status != ReferralStatus.APPROVED:
            raise HTTPException(
                status_code=400, 
                detail="Cannot bind quote: The attached referral must be approved."
            )

    # 3. Execute Quote Action (NO COMMIT)
    quote_response = await updateStatus_quote(
        quote_code=quote_code, 
        status=quote_action, 
        db=db, 
        commit=False
    )

    # 4. Fire both to the DB at once 
    await db.commit()

    return {
        "status": "success",
        "message": "Workflow resolved atomically",
        "referral_update": ref_response,
        "quote_update": quote_response
    }