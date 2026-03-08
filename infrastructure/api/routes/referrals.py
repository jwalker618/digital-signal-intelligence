"""
DSI Referral Endpoints (Phase 8/11) - Database Backed

Endpoints for managing underwriter referrals and signal overrides.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote,
    Referral,
    ReferralStatus,
)

from ..types import (
    ReferralRecord,
)

logger = logging.getLogger("dsi.api.referrals")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/referrals/{referral_code}", response_model=ReferralRecord)
async def get_referral(
    referral_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ReferralRecord:
    """Get referral details by code.."""
    query = select(Referral).where(Referral.referral_code == referral_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Referral not found")

    return record

@router.post("/referrals/{quote_code}/update-status")
async def updateStatus_referral(
    quote_code: str,
    status: ReferralStatus,
    db: AsyncSession = Depends(get_async_db),
    commit: bool = True
) -> Dict[str, Any]:
    
    """Update the status of a referral."""
    query = (select(Referral).join(Quote, Referral.quote_id == Quote.id).where(Quote.quote_code == quote_code))
    q = (await db.execute(query)).scalar_one_or_none()
    
    # Auto-approved or clean quotes won't have a referral
    if not q:
        return {
            "status": "error",
            "message": "Referral not found",
            "referral_code": quote_code,
        }

    if q.status != ReferralStatus.IN_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Referral cannot be updated in current status: {q.status.value}",
        )

    q.status = status
    if commit:
        await db.commit()

    return {
        "status": "success",
        "message": f"Referral status: {q.status.value}",
        "referral_code": q.referral_code,
        "updated_at": q.updated_at,
    }

@router.get("/referrals/summary/queue")
async def get_queue_summary(
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Get a quick summary of the pending referral queue."""
    query = (
        select(func.count(Referral.referral_code), func.min(Referral.created_at))
        .where(Referral.status == ReferralStatus.PENDING)
    )
    result = (await db.execute(query)).first()
    count = result[0] or 0
    oldest = result[1]

    if oldest:
        oldest_hours = (
            datetime.now(timezone.utc) - oldest.replace(tzinfo=timezone.utc)
        ).total_seconds() / 3600
    else:
        oldest_hours = 0.0

    return {
        "pending_count": count,
        "oldest_hours": round(oldest_hours, 1),
    }

@router.get("/referrals/stats")
async def get_referral_stats(
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Aggregate referral DB statistics."""
    query = select(Referral.status, func.count(Referral.referral_code)).group_by(Referral.status)
    rows = (await db.execute(query)).all()

    stats: Dict[str, int] = {
        "pending": 0,
        "approved": 0,
        "declined": 0,
        "modified": 0,
        "in_review": 0,
    }
    total = 0

    for status_enum, count in rows:
        stats[status_enum.value] = count
        total += count

    resolved = stats["approved"] + stats["declined"] + stats["modified"]
    
    return {
        "statuses": stats,
        "total": total,
        "resolved": resolved,
        "resolution_rate": resolved / total if total > 0 else 0,
    }

