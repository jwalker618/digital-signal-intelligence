"""
DSI Referral Endpoints (Phase 8/11) - Database Backed

Endpoints for managing underwriter referrals and signal overrides.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Referral,
    ReferralStatus as DBReferralStatus,
)
from ..types import (
    ReferralRecord,
)

logger = logging.getLogger("dsi.api.referrals")
router = APIRouter()


# =============================================================================
# UTILITIES
# =============================================================================

def generate_id(prefix: str) -> str:
    """Generate a unique string ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _parse_json(val: Any, default: Any = None) -> Any:
    """Safely parse PostgreSQL JSONB into Python dicts/lists."""
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (TypeError, ValueError):
        return default


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/referrals/{referral_code}", response_model=ReferralRecord)
async def get_referral(
    referral_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ReferralRecord:
    """Get referral details by code.."""
    query = select(ReferralRecord).where(ReferralRecord.referral_code == referral_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    return ReferralRecord(
        referral_code=row.referral_code,
        status=row.status,
        reasons=row.reasons,
        priority=row.priority,
        review_decision=row.review_decision,
        review_notes=row.review_notes,
        tier_override=row.tier_override,
        premium_adjustment=row.premium_adjustment,
        adjustments=row.adjustments,
    )

@router.get("/referrals/summary/queue")
async def get_queue_summary(
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Get a quick summary of the pending referral queue."""
    query = (
        select(func.count(Referral.id), func.min(Referral.created_at))
        .where(Referral.status == DBReferralStatus.PENDING)
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
    query = select(Referral.status, func.count(Referral.id)).group_by(
        Referral.status
    )
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