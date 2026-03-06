"""
DSI Quote Endpoints (Phase 11) - Database Backed

Endpoints for retrieving and managing quotes.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote,
    Submission,
    ModelVersionRecord,
    Referral,
    QuoteStatus,
    DecisionType
)
from ..types import (
    QuoteResponse,
    QuoteListItem,
    DiscoverySummary,
    SignalSummary,
    LossPropensitySummary,
    ExposureSummary,
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
        return default if default is not None else {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (TypeError, json.JSONDecodeError):
        return default if default is not None else {}

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/quotes", response_model=List[QuoteListItem])
async def list_quotes(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_db)
):
    """List quotes strictly from the database."""
    query = select(Quote, Submission, ModelVersionRecord).join(
        Submission, Quote.submission_id == Submission.id
    ).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    )

    if coverage:
        query = query.where(Submission.coverage == coverage)

    if status:
        try:
            db_status = QuoteStatus(status.lower())
            query = query.where(Quote.status == db_status)
        except ValueError:
            pass

    query = query.order_by(Quote.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    rows = result.all()

    return [
        QuoteListItem(
            quote_id=q.quote_id,
            submission_id=s.submission_id,
            model_version_id=mv.version_id,
            entity_name=s.entity_name,
            coverage=s.coverage,
            status=q.status.value,
            tier=mv.final_tier or 0,
            premium=q.recommended_premium or 0.0,
            decision=mv.decision.value if mv.decision else "refer",
            created_at=q.created_at
        )
        for q, s, mv in rows
    ]


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get full quote details, joining the ModelVersionRecord for pricing logic."""
    query = select(Quote, Submission, ModelVersionRecord).join(
        Submission, Quote.submission_id == Submission.id
    ).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).where(Quote.quote_id == quote_id)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    q, sub, mv = row

    # Map JSONB / Nested fields safely with fallbacks for dirty DB data
    discovery_data = _parse_json(mv.discovery_output, {})
    if discovery_data:
        discovery = DiscoverySummary(
            domain=discovery_data.get("domain", "unknown"),
            confidence=discovery_data.get("confidence", "low"),
            # Often older ML outputs use 'inferred' instead of 'industry'
            industry=discovery_data.get("industry") or discovery_data.get("inferred"), 
            employee_count=discovery_data.get("employee_count")
        )
    else:
        discovery = None

    # Calculate Signal Summary safely
    signals = _parse_json(mv.signal_outputs, [])
    top_factors = []
    if signals:
        sorted_signals = sorted(signals, key=lambda x: abs(x.get('contribution', 0)), reverse=True)[:3]
        top_factors = [{"signal": s.get("name"), "impact": "positive" if s.get("contribution", 0) > 0 else "negative", "score": s.get("value")} for s in sorted_signals]
    
    signal_summary = SignalSummary(
        total_signals=mv.signal_coverage * 100 if mv.signal_coverage else len(signals),
        signals_extracted=len(signals),
        top_factors=top_factors
    ) if signals else None

    loss_propensity = LossPropensitySummary(
        loss_propensity_score=mv.loss_propensity_score,
        severity_propensity_score=mv.severity_propensity_score,
        loss_propensity_band=mv.loss_propensity_band,
        severity_propensity_band=mv.severity_propensity_band,
        loss_confidence=mv.loss_confidence,
        loss_combined_modifier=mv.loss_combined_modifier,
        loss_cohort_name=mv.loss_cohort_name,
        loss_trend_direction=mv.loss_trend_direction
    ) if mv.loss_propensity_score is not None else None

    exposure = ExposureSummary(
        exposure_value=mv.exposure_value,
        exposure_band_label=mv.exposure_band_label,
        exposure_magnitude_score=mv.exposure_magnitude_score,
        exposure_modifier=mv.exposure_modifier
    ) if mv.exposure_value is not None else None

    # Check for active referral
    ref_query = select(Referral).where(Referral.quote_id == q.id).order_by(Referral.created_at.desc()).limit(1)
    ref = (await db.execute(ref_query)).scalar_one_or_none()

    return QuoteResponse(
        quote_id=q.quote_id,
        submission_id=sub.submission_id,
        model_version_id=mv.version_id,
        status=q.status.value,
        composite_score=int(mv.pure_composite_score or 0),
        tier=mv.final_tier or 0,
        tier_label=mv.tier_label or "UNKNOWN",
        decision=mv.decision.value if mv.decision else "refer",
        premium_options=_parse_json(q.premium_options, {}),
        recommended_premium=q.recommended_premium,
        recommended_limit=q.recommended_limit,
        base_premium=mv.base_premium,
        premium_after_modifiers=mv.premium_after_modifiers,
        modifiers_applied=_parse_json(mv.modifiers_applied, []),
        loss_propensity=loss_propensity,
        exposure=exposure,
        discovery=discovery,
        signal_summary=signal_summary,
        referral_reasons=_parse_json(mv.referral_reasons, []),
        referral_id=ref.referral_id if ref else None,
        valid_until=q.valid_until,
        created_at=q.created_at,
    )


@router.post("/quotes/{quote_id}/bind")
async def bind_quote(quote_id: str, db: AsyncSession = Depends(get_async_db)):
    """Bind a quote atomically."""
    query = select(Quote).where(Quote.quote_id == quote_id)
    q = (await db.execute(query)).scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    if q.status != QuoteStatus.READY:
        raise HTTPException(status_code=400, detail=f"Cannot bind quote in status {q.status.value}")

    # Ensure validity is naive or converted to UTC for correct comparison
    now = datetime.now(timezone.utc)
    valid_until = q.valid_until.replace(tzinfo=timezone.utc) if q.valid_until.tzinfo is None else q.valid_until
    
    if valid_until < now:
        q.status = QuoteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Quote has expired")

    q.status = QuoteStatus.BOUND
    q.bound_at = now
    policy_num = generate_id("pol")
    q.policy_number = policy_num
    
    await db.commit()

    return {
        "message": "Quote bound successfully",
        "quote_id": quote_id,
        "policy_id": policy_num,
        "bound_at": q.bound_at,
    }


@router.post("/quotes/{quote_id}/decline")
async def decline_quote(
    quote_id: str, 
    reason: Optional[str] = None, 
    db: AsyncSession = Depends(get_async_db)
):
    """Decline a quote atomically."""
    query = select(Quote).where(Quote.quote_id == quote_id)
    q = (await db.execute(query)).scalar_one_or_none()

    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    if q.status not in [QuoteStatus.READY, QuoteStatus.DRAFT]:
        raise HTTPException(status_code=400, detail=f"Cannot decline quote in status {q.status.value}")

    q.status = QuoteStatus.DECLINED
    q.updated_at = datetime.now(timezone.utc)
    # The DB model doesn't explicitly have a `decline_reason` on Quote, 
    # but it maps to the status seamlessly.
    
    await db.commit()

    return {
        "message": "Quote declined",
        "quote_id": quote_id,
        "declined_at": q.updated_at,
    }


@router.get("/quotes/{quote_id}/premium-options")
async def get_premium_options(
    quote_id: str,
    limits: Optional[List[int]] = Query(None, description="Specific limits to price"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get or calculate premium options based on the underlying tier."""
    query = select(Quote, ModelVersionRecord).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).where(Quote.quote_id == quote_id)
    
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    q, mv = row
    
    if limits:
        # Dynamic recalculation using DB Tier
        base_rate = 0.00625
        tier_factor = {1: 0.8, 2: 1.0, 3: 1.2, 4: 1.5, 5: 2.0}.get(mv.final_tier, 1.0)

        options = {}
        for limit in limits:
            premium = limit * base_rate * tier_factor
            options[str(limit)] = round(premium, 2)

        return {"quote_id": quote_id, "premium_options": options}

    return {
        "quote_id": quote_id,
        "premium_options": _parse_json(q.premium_options, {}),
        "recommended_limit": q.recommended_limit,
        "recommended_premium": q.recommended_premium,
    }