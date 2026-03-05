"""
DSI Quote Endpoints (Phase 11)

Endpoints for retrieving and managing quotes.
Wired to database repositories (Phase 8).
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..types import (
    QuoteResponse,
    QuoteListItem,
    QuoteStatus,
    DiscoverySummary,
    SignalSummary,
    LossPropensitySummary,
    ExposureSummary,
)
from ...db.config import get_async_db
from ...db.models import (
    Quote,
    Submission,
    ModelVersionRecord,
    QuoteStatus as DBQuoteStatus,
)
from ...db.repositories import QuoteRepository, AuditLogRepository


logger = logging.getLogger("dsi.api.quotes")

router = APIRouter()


# =============================================================================
# HELPERS
# =============================================================================

_DB_TO_API_STATUS = {
    DBQuoteStatus.DRAFT: QuoteStatus.PENDING,
    DBQuoteStatus.READY: QuoteStatus.READY,
    DBQuoteStatus.BOUND: QuoteStatus.BOUND,
    DBQuoteStatus.EXPIRED: QuoteStatus.EXPIRED,
    DBQuoteStatus.DECLINED: QuoteStatus.DECLINED,
}


def _map_quote_status(db_status: DBQuoteStatus) -> QuoteStatus:
    """Map DB QuoteStatus to API QuoteStatus."""
    return _DB_TO_API_STATUS.get(db_status, QuoteStatus.PENDING)


def _build_quote_response(
    quote: Quote,
    mv: ModelVersionRecord,
    submission: Submission,
) -> QuoteResponse:
    """Build a QuoteResponse from DB models."""
    # Discovery summary
    discovery = None
    if mv.discovery_output and isinstance(mv.discovery_output, dict):
        discovery = DiscoverySummary(
            domain=mv.discovery_output.get("domain", "unknown"),
            confidence=mv.discovery_output.get("confidence", "low"),
            industry=mv.discovery_output.get("industry"),
            employee_count=mv.discovery_output.get("employee_count"),
        )

    # Signal summary
    signal_summary = None
    if mv.signal_outputs:
        sig_list = mv.signal_outputs if isinstance(mv.signal_outputs, list) else []
        signal_summary = SignalSummary(
            total_signals=len(sig_list),
            signals_extracted=len(sig_list),
            top_factors=sig_list[:3] if sig_list else [],
        )

    # Loss propensity
    loss_propensity = None
    if mv.loss_propensity_score is not None:
        loss_propensity = LossPropensitySummary(
            loss_propensity_score=mv.loss_propensity_score,
            severity_propensity_score=mv.severity_propensity_score,
            loss_propensity_band=mv.loss_propensity_band,
            severity_propensity_band=mv.severity_propensity_band,
            loss_confidence=mv.loss_confidence,
            loss_combined_modifier=mv.loss_combined_modifier,
            loss_cohort_name=mv.loss_cohort_name,
            loss_trend_direction=mv.loss_trend_direction,
        )

    # Exposure
    exposure = None
    if mv.exposure_value is not None:
        exposure = ExposureSummary(
            exposure_value=mv.exposure_value,
            exposure_band_label=mv.exposure_band_label,
            exposure_magnitude_score=mv.exposure_magnitude_score,
            exposure_modifier=mv.exposure_modifier,
        )

    # Determine referral_id if any active referral exists
    referral_id = None
    if hasattr(quote, "referrals") and quote.referrals:
        for ref in quote.referrals:
            if ref.status.value in ("pending", "in_review"):
                referral_id = ref.referral_id
                break

    return QuoteResponse(
        quote_id=quote.quote_id,
        submission_id=submission.submission_id,
        status=_map_quote_status(quote.status),
        composite_score=int(mv.pure_composite_score or 0),
        tier=mv.final_tier or 0,
        tier_label=mv.tier_label or "UNKNOWN",
        decision=mv.decision.value if mv.decision else "refer",
        premium_options=quote.premium_options or {},
        recommended_premium=quote.recommended_premium,
        recommended_limit=quote.recommended_limit,
        base_premium=mv.base_premium,
        premium_after_modifiers=mv.premium_after_modifiers,
        modifiers_applied=mv.modifiers_applied or [],
        loss_propensity=loss_propensity,
        exposure=exposure,
        discovery=discovery,
        signal_summary=signal_summary,
        referral_reasons=mv.referral_reasons or [],
        referral_id=referral_id,
        valid_until=quote.valid_until,
        created_at=quote.created_at,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/quotes", response_model=List[QuoteListItem])
async def list_quotes(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List quotes with optional filtering.
    """
    query = (
        select(Quote)
        .join(Quote.submission)
        .join(Quote.model_version)
        .options(
            selectinload(Quote.submission),
            selectinload(Quote.model_version),
        )
    )

    if coverage:
        query = query.where(Submission.coverage == coverage)

    if status:
        api_to_db = {
            "pending": DBQuoteStatus.DRAFT,
            "ready": DBQuoteStatus.READY,
            "bound": DBQuoteStatus.BOUND,
            "expired": DBQuoteStatus.EXPIRED,
            "declined": DBQuoteStatus.DECLINED,
        }
        db_status = api_to_db.get(status)
        if db_status:
            query = query.where(Quote.status == db_status)

    query = query.order_by(Quote.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    quotes = list(result.scalars().all())

    return [
        QuoteListItem(
            quote_id=q.quote_id,
            submission_id=q.submission.submission_id,
            entity_name=q.submission.entity_name,
            coverage=q.submission.coverage,
            status=_map_quote_status(q.status),
            tier=q.model_version.final_tier or 0,
            premium=q.recommended_premium or 0,
            decision=q.model_version.decision.value if q.model_version.decision else "refer",
            created_at=q.created_at,
        )
        for q in quotes
    ]


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get quote details by ID.
    """
    result = await db.execute(
        select(Quote)
        .where(Quote.quote_id == quote_id)
        .options(
            selectinload(Quote.submission),
            selectinload(Quote.model_version),
        )
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    return _build_quote_response(quote, quote.model_version, quote.submission)


@router.post("/quotes/{quote_id}/bind")
async def bind_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Bind a quote (convert to policy).
    """
    repo = QuoteRepository(db)
    quote = await repo.get_by_id(quote_id)

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status != DBQuoteStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot bind quote in status {quote.status.value}",
        )

    if quote.valid_until and quote.valid_until < datetime.utcnow():
        await repo.update_status(quote_id, DBQuoteStatus.EXPIRED)
        raise HTTPException(status_code=400, detail="Quote has expired")

    policy_number = f"POL-{uuid.uuid4().hex[:8].upper()}"
    bound_quote = await repo.bind(
        quote_id=quote_id,
        bound_by=uuid.uuid4(),  # placeholder — real user from auth context
        policy_number=policy_number,
    )

    audit_repo = AuditLogRepository(db)
    await audit_repo.log(
        event_type="quote",
        event_action="bind",
        resource_type="quote",
        resource_id=quote_id,
        details={"policy_number": policy_number},
    )

    return {
        "message": "Quote bound successfully",
        "quote_id": quote_id,
        "policy_id": policy_number,
        "bound_at": bound_quote.bound_at,
    }


@router.post("/quotes/{quote_id}/decline")
async def decline_quote(
    quote_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Decline a quote.
    """
    repo = QuoteRepository(db)
    quote = await repo.get_by_id(quote_id)

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status not in (DBQuoteStatus.READY, DBQuoteStatus.DRAFT):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot decline quote in status {quote.status.value}",
        )

    await repo.update_status(quote_id, DBQuoteStatus.DECLINED)

    audit_repo = AuditLogRepository(db)
    await audit_repo.log(
        event_type="quote",
        event_action="decline",
        resource_type="quote",
        resource_id=quote_id,
        details={"reason": reason},
    )

    return {
        "message": "Quote declined",
        "quote_id": quote_id,
        "declined_at": datetime.utcnow(),
    }


@router.get("/quotes/{quote_id}/signals")
async def get_quote_signals(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get detailed signal breakdown for a quote.
    """
    result = await db.execute(
        select(Quote)
        .where(Quote.quote_id == quote_id)
        .options(selectinload(Quote.model_version))
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    mv = quote.model_version
    signal_groups: dict = {}

    if mv and mv.signal_outputs:
        for sig in (mv.signal_outputs if isinstance(mv.signal_outputs, list) else []):
            group = sig.get("group_id", "other")
            if group not in signal_groups:
                signal_groups[group] = {
                    "weight": sig.get("group_weight", 0.20),
                    "signals": [],
                }
            signal_groups[group]["signals"].append({
                "id": sig.get("signal_id", "unknown"),
                "score": sig.get("score", 0),
                "contribution": sig.get("contribution", 0),
            })

    return {"quote_id": quote_id, "signal_groups": signal_groups}


@router.get("/quotes/{quote_id}/premium-options")
async def get_premium_options(
    quote_id: str,
    limits: Optional[List[int]] = Query(None, description="Specific limits to price"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get premium options for various limits.
    """
    result = await db.execute(
        select(Quote)
        .where(Quote.quote_id == quote_id)
        .options(selectinload(Quote.model_version))
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if limits:
        tier = quote.model_version.final_tier if quote.model_version else 3
        base_rate = 0.00625
        tier_factor = {1: 0.8, 2: 1.0, 3: 1.2, 4: 1.5, 5: 2.0}.get(tier, 1.0)

        options = {}
        for limit_val in limits:
            premium = limit_val * base_rate * tier_factor
            options[str(limit_val)] = round(premium, 2)

        return {"quote_id": quote_id, "premium_options": options}

    return {
        "quote_id": quote_id,
        "premium_options": quote.premium_options or {},
        "recommended_limit": quote.recommended_limit,
        "recommended_premium": quote.recommended_premium,
    }
