"""
DSI Referral Endpoints (Phase 8/11) - Database Backed

Endpoints for managing underwriter referrals and signal overrides.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Referral,
    Quote,
    Submission,
    ModelVersionRecord,
    ModelVersionSignal,
    SignalCache,
    SignalAuditRecord,
    ReferralStatus as DBReferralStatus,
    DecisionType as DBDecisionType,
    QuoteStatus as DBQuoteStatus,
)
from ..types import (
    ReferralDecision,
    ReferralDecisionType,
    ReferralRecord,
    ReferralListItem,
    QuoteResponse,
    SignalOverrideRequest,
    SignalOverrideResponse,
    ReferralSignalDetail,
    ReferralSignalsResponse,
    ModelVersionResponse,
    ReferralStatus,
    DecisionType,
    QuoteStatus,
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

@router.get("/referrals", response_model=List[ReferralListItem])
async def list_referrals(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
) -> List[ReferralListItem]:
    """List referrals for underwriter review."""
    query = (
        select(Referral, Submission)
        .join(Submission, Referral.submission_id == Submission.id)
        .order_by(Referral.priority.asc(), Referral.created_at.desc())
    )

    if status:
        query = query.where(Referral.status == DBReferralStatus(status))

    query = query.offset(offset).limit(limit)
    rows = (await db.execute(query)).all()

    results = []
    now = datetime.now(timezone.utc)
    for ref, sub in rows:
        created_utc = ref.created_at.replace(tzinfo=timezone.utc) if ref.created_at else now
        age_hours = (now - created_utc).total_seconds() / 3600

        results.append(
            ReferralListItem(
                referral_id=ref.referral_id,
                entity_name=sub.entity_name,
                coverage=sub.coverage,
                status=ReferralStatus(ref.status.value),
                reasons=_parse_json(ref.reasons, []),
                age_hours=round(age_hours, 1),
                created_at=ref.created_at,
            )
        )

    return results


@router.get("/referrals/{referral_id}", response_model=ReferralRecord)
async def get_referral(
    referral_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> ReferralRecord:
    """Get referral details."""
    query = (
        select(Referral, Submission)
        .join(Submission, Referral.submission_id == Submission.id)
        .where(Referral.referral_id == referral_id)
    )

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    ref, sub = row

    return ReferralRecord(
        referral_id=ref.referral_id,
        quote_id=ref.quote_id,
        submission_id=sub.submission_id,
        entity_name=sub.entity_name,
        coverage=sub.coverage,
        status=ReferralStatus(ref.status.value),
        reasons=_parse_json(ref.reasons, []),
        original_tier=ref.original_tier,
        original_score=ref.original_score,
        original_premium=ref.original_premium,
        reviewed_at=ref.reviewed_at,
        review_notes=_parse_json(ref.review_notes, []),
        tier_override=ref.tier_override,
        premium_adjustment=ref.premium_adjustment,
        created_at=ref.created_at,
    )


@router.get("/referrals/{referral_id}/signals", response_model=ReferralSignalsResponse)
async def get_referral_signals(
    referral_id: str,
    include_raw: bool = Query(False),
    db: AsyncSession = Depends(get_async_db),
) -> ReferralSignalsResponse:
    """Get detailed signal inputs for a referral's active model version."""
    query = (
        select(Referral, Quote, ModelVersionRecord)
        .join(Quote, Referral.quote_id == Quote.id)
        .join(ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id)
        .where(Referral.referral_id == referral_id)
    )
    
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral or Model not found")

    ref, q, mv = row

    sig_query = (
        select(ModelVersionSignal, SignalCache, SignalAuditRecord)
        .join(SignalCache, ModelVersionSignal.signal_cache_id == SignalCache.id)
        .outerjoin(
            SignalAuditRecord,
            and_(
                ModelVersionSignal.signal_id == SignalAuditRecord.signal_id,
                ModelVersionSignal.entity_id == SignalAuditRecord.entity_id,
            ),
        )
        .where(ModelVersionSignal.model_version_id == mv.id)
    )

    sig_rows = (await db.execute(sig_query)).all()

    signals = []
    
    def _extract_val(field, default=0.0):
        if field is None:
            return default
        if isinstance(field, dict):
            for k in ["value", "audited_value", "inferred_value"]:
                if k in field:
                    return float(field[k])
            return default
        try:
            return float(field)
        except (ValueError, TypeError):
            return default

    for mvs, sc, sar in sig_rows:
        data = _parse_json(sc.data, {})
        inferred = _extract_val(sc.inferred_value, _extract_val(data, 0.0))
        audited = _extract_val(sar.audited_value) if sar and sar.is_overridden else None

        signals.append(
            ReferralSignalDetail(
                signal_cache_id=str(sc.id),
                signal_id=mvs.signal_id,
                signal_name=data.get("name", mvs.signal_id),
                group_id=mvs.group_id or data.get("group_id", "general"),
                group_name=data.get("group_name", "General"),
                score=float(mvs.score) if mvs.score is not None else inferred,
                inferred_value=inferred,
                audited_value=audited,
                is_overridden=bool(sar and sar.is_overridden),
                weight=float(mvs.weight) if mvs.weight is not None else float(data.get("weight", 0.1)),
                contribution_to_score=float(mvs.contribution) if mvs.contribution is not None else float(data.get("contribution", 0.0)),
                is_flagged=data.get("is_flagged", False),
                flag_reason=data.get("flag_reason"),
                confidence=sc.confidence or 1.0,
                data_sources=data.get("sources", []),
                extracted_at=sc.extracted_at,
                raw_data=data if include_raw else None,
                in_model=True,
                proxy_tier=mvs.proxy_tier,
                expectation_level=mvs.expectation_level,
                was_absent=mvs.was_absent,
                used_audited_value=mvs.used_audited_value,
                override_rationale=sar.override_rationale if sar else None,
                evidence_reference=sar.evidence_reference if sar else None,
                score_impact=sar.score_impact if sar else None,
                tier_impact=sar.tier_impact if sar else None,
            )
        )

    overridden_count = sum(1 for s in signals if s.is_overridden)
    flagged_count = sum(1 for s in signals if s.is_flagged)
    avg_conf = sum(s.confidence for s in signals) / len(signals) if signals else 1.0

    return ReferralSignalsResponse(
        referral_id=ref.referral_id,
        model_version_id=mv.version_id,
        configuration_name=mv.configuration_name,
        coverage=mv.coverage,
        signals=signals,
        flagged_count=flagged_count,
        overridden_count=overridden_count,
        total_signals=len(signals),
        model_signal_count=len(signals),
        signal_coverage=mv.signal_coverage or 1.0,
        average_confidence=avg_conf,
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