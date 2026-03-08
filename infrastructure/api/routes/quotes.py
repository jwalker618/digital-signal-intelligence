"""
DSI Quote Endpoints (Phase 11) - Database Backed

Endpoints for retrieving and managing quotes.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote,
    Submission,
    ModelVersionRecord,
    Referral,
    QuoteStatus as DBQuoteStatus,
    DecisionType as DBDecisionType,
)
from ..types import (
    QuoteResponse,
    QuoteListItem,
    DiscoverySummary,
    SignalSummary,
    LossPropensitySummary,
    ExposureSummary,
    QuoteStatus,
    DecisionType,
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


@router.get("/quotes", response_model=List[QuoteListItem])
async def list_quotes(
    status: Optional[str] = Query(None, description="Filter by quote status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
) -> List[QuoteListItem]:
    """List quotes with optional filtering."""
    query = (
        select(Quote, Submission, ModelVersionRecord)
        .join(Submission, Quote.submission_id == Submission.id)
        .outerjoin(ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id)
        .order_by(Quote.created_at.desc())
    )

    if status:
        query = query.where(Quote.status == DBQuoteStatus(status))

    query = query.offset(offset).limit(limit)
    rows = (await db.execute(query)).all()

    results = []
    for q, s, mv in rows:
        results.append(
            QuoteListItem(
                quote_id=q.quote_id,
                submission_id=s.submission_id,
                model_version_id=mv.version_id if mv else None,
                entity_name=s.entity_name,
                coverage=s.coverage,
                status=QuoteStatus(q.status.value),
                tier=mv.final_tier if mv else 0,
                premium=q.recommended_premium or 0.0,
                decision=DecisionType(mv.decision.value) if mv and mv.decision else DecisionType.REFER,
                created_at=q.created_at,
            )
        )

    return results


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> QuoteResponse:
    """Get detailed quote information combining Model outputs and DB rows."""
    query = (
        select(Quote, Submission, ModelVersionRecord, Referral)
        .join(Submission, Quote.submission_id == Submission.id)
        .outerjoin(ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id)
        .outerjoin(Referral, Referral.quote_id == Quote.id)
        .where(Quote.quote_id == quote_id)
    )

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    q, s, mv, ref = row

    # Extract dynamic properties
    signal_summary = None
    loss_prop = None
    exposure = None
    discovery = None

    if mv:
        loss_prop = LossPropensitySummary(
            loss_propensity_score=mv.loss_propensity_score,
            severity_propensity_score=mv.severity_propensity_score,
            loss_propensity_band=mv.loss_propensity_band,
            severity_propensity_band=mv.severity_propensity_band,
            loss_confidence=mv.loss_confidence,
            loss_combined_modifier=mv.loss_combined_modifier,
            loss_cohort_name=mv.loss_cohort_name,
            loss_trend_direction=mv.loss_trend_direction,
        )

        exposure = ExposureSummary(
            exposure_value=mv.exposure_value,
            exposure_band_label=mv.exposure_band_label,
            exposure_magnitude_score=mv.exposure_magnitude_score,
            exposure_modifier=mv.exposure_modifier,
        )

        disc_out = _parse_json(mv.discovery_output, {})
        discovery = DiscoverySummary(
            domain=disc_out.get("domain", s.domain_hint or ""),
            confidence=disc_out.get("confidence", "unknown"),
            industry=disc_out.get("industry"),
            employee_count=disc_out.get("employee_count"),
        )

        signal_summary = SignalSummary(
            total_signals=mv.signal_coverage,
            signals_extracted=mv.signal_coverage,
            top_factors=[],  
        )

    return QuoteResponse(
        quote_id=q.quote_id,
        submission_id=s.submission_id,
        model_version_id=mv.version_id if mv else None,
        status=QuoteStatus(q.status.value),
        composite_score=int(mv.pure_composite_score) if mv and mv.pure_composite_score else 0,
        tier=mv.final_tier if mv else 0,
        tier_label=mv.tier_label if mv else "Unknown",
        decision=DecisionType(mv.decision.value) if mv and mv.decision else DecisionType.REFER,
        premium_options=_parse_json(q.premium_options, {}),
        recommended_premium=q.recommended_premium,
        recommended_limit=q.recommended_limit,
        base_premium=mv.base_premium if mv else None,
        premium_after_modifiers=mv.premium_after_modifiers if mv else None,
        modifiers_applied=_parse_json(mv.modifiers_applied, []) if mv else [],
        loss_propensity=loss_prop,
        exposure=exposure,
        discovery=discovery,
        signal_summary=signal_summary,
        referral_reasons=_parse_json(mv.referral_reasons, []) if mv else [],
        referral_id=ref.referral_id if ref else None,
        valid_until=q.valid_until,
        created_at=q.created_at,
    )


@router.post("/quotes/{quote_id}/bind")
async def bind_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Bind a quote (convert to policy)."""
    query = select(Quote).where(Quote.quote_id == quote_id)
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
        "quote_id": quote_id,
        "policy_number": q.policy_number,
        "bound_at": q.bound_at,
    }


@router.post("/quotes/{quote_id}/decline")
async def decline_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Decline a quote (customer rejection)."""
    query = select(Quote).where(Quote.quote_id == quote_id)
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
        "quote_id": quote_id,
        "declined_at": q.updated_at,
    }


@router.get("/quotes/{quote_id}/premium-options")
async def get_premium_options(
    quote_id: str,
    limits: Optional[List[int]] = Query(
        None,
        description="Specific limits to price",
    ),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Get or calculate premium options based on the underlying tier."""
    query = (
        select(Quote, ModelVersionRecord)
        .join(ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id)
        .where(Quote.quote_id == quote_id)
    )

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    q, mv = row

    if limits:
        base_rate = 0.00625
        tier_factor = {
            1: 0.8,
            2: 1.0,
            3: 1.2,
            4: 1.5,
            5: 2.0,
        }.get(mv.final_tier, 1.0)

        options: Dict[str, float] = {}
        for limit in limits:
            pure_premium = limit * base_rate * tier_factor
            options[str(limit)] = round(pure_premium, 2)

        return {"quote_id": quote_id, "options": options}

    return {
        "quote_id": quote_id,
        "options": _parse_json(q.premium_options, {}),
    }