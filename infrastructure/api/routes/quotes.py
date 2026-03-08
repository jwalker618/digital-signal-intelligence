"""
DSI Quote Endpoints (Phase 11) - Database Backed

Endpoints for retrieving and managing quotes.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    QuoteStatus as DBQuoteStatus,
)
from ..types import (
    QuoteRecord
)

logger = logging.getLogger("dsi.api.quotes")
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

@router.get("/quotes/{quote_code}", response_model=QuoteRecord)
async def get_quote(
    quote_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> QuoteRecord:
    """Get quote details by code."""
    query = select(QuoteRecord).where(QuoteRecord.quote_code == quote_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    return QuoteRecord(
        quote_code=row.quote_code,
        status=row.status,
        recommended_premium=row.recommended_premium,
        recommended_limit=row.recommended_limit,
        premium_options=row.premium_options,
        valid_from=row.valid_from,
        valid_until=row.valid_until,
        bound_at=row.bound_at,
        bound_by=row.bound_by,
        policy_number=row.policy_number,     
    )


@router.post("/quotes/{quote_code}/bind")
async def bind_quote(
    quote_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Bind a quote (convert to policy)."""
    query = select(QuoteRecord).where(QuoteRecord.quote_code == quote_code)
    q = (await db.execute(query)).scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    if q.status != DBQuoteStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Quote cannot be bound in current status: {q.status.value}",
        )

    if q.valid_until and q.valid_until < datetime.now(timezone.utc):
        q.status = DBQuoteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Quote has expired")

    q.status = DBQuoteStatus.BOUND
    q.bound_at = datetime.now(timezone.utc)
    q.policy_number = generate_id("pol")
    await db.commit()

    return {
        "status": "success",
        "message": "Quote successfully bound",
        "quote_code": quote_code,
        "policy_number": q.policy_number,
        "bound_at": q.bound_at,
    }


@router.post("/quotes/{quote_code}/decline")
async def decline_quote(
    quote_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Decline a quote (customer rejection)."""
    query = select(QuoteRecord).where(QuoteRecord.quote_code == quote_code)
    q = (await db.execute(query)).scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    if q.status != DBQuoteStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Quote cannot be declined in current status: {q.status.value}",
        )

    q.status = DBQuoteStatus.DECLINED
    await db.commit()

    return {
        "status": "success",
        "message": "Quote declined",
        "quote_code": quote_code,
        "declined_at": q.updated_at,
    }