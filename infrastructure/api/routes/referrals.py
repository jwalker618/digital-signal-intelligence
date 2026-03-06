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
from sqlalchemy import select, and_, func, update

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Referral,
    Quote,
    Submission,
    ModelVersionRecord,
    SignalCache,
    SignalAuditRecord,
    ReferralStatus,
    DecisionType,
    QuoteStatus
)
from ..types import (
    ReferralDecision,
    ReferralDecisionType,
    ReferralDetail,
    ReferralListItem,
    QuoteResponse,
    SignalOverrideRequest,
    SignalOverrideResponse,
    ReferralSignalDetail,
    ReferralSignalsResponse,
    ModelVersionResponse,
)

logger = logging.getLogger("dsi.api.referrals")
router = APIRouter()

# =============================================================================
# UTILITIES
# =============================================================================

def generate_id(prefix: str) -> str:
    """Generate a unique string ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def safe_uuid(val: Optional[str]) -> Optional[uuid.UUID]:
    """Safely convert a string to UUID for foreign keys."""
    if not val or val == "unknown":
        return None
    try:
        return uuid.UUID(val)
    except ValueError:
        return None

def _parse_string_list(val) -> List[str]:
    """Safely parse DB JSONB/Text arrays into Python Lists."""
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except (TypeError, json.JSONDecodeError):
        return [str(val)]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/referrals", response_model=List[ReferralListItem])
async def list_referrals(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, declined)"),
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_db)
):
    """List referrals strictly from the database."""
    
    query = select(Referral, Submission).join(
        Quote, Referral.quote_id == Quote.id
    ).join(
        Submission, Quote.submission_id == Submission.id
    )

    if status:
        # Map string to Enum safely
        try:
            db_status = ReferralStatus(status.lower())
            query = query.where(Referral.status == db_status)
        except ValueError:
            pass

    if coverage:
        query = query.where(Submission.coverage == coverage)

    query = query.order_by(Referral.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    rows = result.all()

    items = []
    for ref, sub in rows:
        age = (datetime.now(timezone.utc) - ref.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        items.append(ReferralListItem(
            referral_id=ref.referral_id,
            entity_name=sub.entity_name,
            coverage=sub.coverage,
            status=ref.status.value,
            reasons=_parse_string_list(ref.reasons),
            age_hours=round(age, 1),
            created_at=ref.created_at
        ))
        
    return items

@router.get("/referrals/{referral_id}", response_model=ReferralDetail)
async def get_referral(referral_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get full referral details, spanning Submission, Quote, and Model Version."""
    
    query = select(Referral, Quote, Submission, ModelVersionRecord).join(
        Quote, Referral.quote_id == Quote.id
    ).join(
        Submission, Quote.submission_id == Submission.id
    ).outerjoin(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).where(Referral.referral_id == referral_id)
    
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
        
    ref, quote, sub, mv = row

    return ReferralDetail(
        referral_id=ref.referral_id,
        quote_id=quote.quote_id,
        submission_id=sub.submission_id,
        entity_name=sub.entity_name,
        coverage=sub.coverage,
        status=ref.status.value,
        reasons=_parse_string_list(ref.reasons),
        original_tier=mv.final_tier if mv else 0,
        original_score=int(mv.pure_composite_score) if mv and mv.pure_composite_score else 0,
        original_premium=quote.recommended_premium or 0.0,
        reviewed_at=ref.reviewed_at,
        reviewed_by=str(ref.reviewed_by) if ref.reviewed_by else None,
        review_notes=_parse_string_list(ref.review_notes),
        tier_override=ref.tier_override,
        premium_adjustment=ref.premium_adjustment,
        created_at=ref.created_at
    )


@router.patch("/referrals/{referral_id}", response_model=ReferralDetail)
async def process_referral(
    referral_id: str,
    decision: ReferralDecision,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Process a referral decision. 
    Updates the Referral record and the core ModelVersionRecord atomically.
    """
    query = select(Referral, Quote, ModelVersionRecord).join(
        Quote, Referral.quote_id == Quote.id
    ).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).where(Referral.referral_id == referral_id)
    
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
        
    ref, quote, mv = row

    if ref.status != ReferralStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Referral already resolved with status: {ref.status.value}")

    # 1. Map adjustments & status
    new_status = ReferralStatus.APPROVED if decision.decision in [ReferralDecisionType.APPROVE, ReferralDecisionType.MODIFY] else ReferralStatus.DECLINED
    
    ref.status = new_status
    ref.reviewed_at = datetime.utcnow()
    ref.reviewed_by = safe_uuid(decision.underwriter_id)
    ref.review_notes = json.dumps(decision.notes) if decision.notes else '[]'
    
    if decision.adjustments:
        ref.tier_override = decision.adjustments.get("tier_override")
        ref.premium_adjustment = decision.adjustments.get("premium_adjustment")

    # 2. Update Model Version (The single source of truth)
    mv.decision = DecisionType(decision.decision.value)

    # 3. Update Quote Status
    quote.status = QuoteStatus.READY if new_status == ReferralStatus.APPROVED else QuoteStatus.DECLINED

    await db.commit()
    
    # Re-fetch via the existing endpoint logic to guarantee Pydantic validation
    return await get_referral(referral_id, db)


# =============================================================================
# PHASE 8: DETERMINISTIC SIGNAL MANAGEMENT
# =============================================================================

@router.get("/referrals/{referral_id}/signals", response_model=ReferralSignalsResponse)
async def get_referral_signals(
    referral_id: str,
    include_all: bool = Query(False, description="Include all signals, not just flagged"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get signals for a referral. 
    Cross-references SignalCache (inferred) with SignalAuditRecord (audited).
    """
    # 1. Fetch Referral Hierarchy
    hierarchy_q = select(Referral, Quote, ModelVersionRecord, Submission).join(
        Quote, Referral.quote_id == Quote.id
    ).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).join(
        Submission, Quote.submission_id == Submission.id
    ).where(Referral.referral_id == referral_id)
    
    row = (await db.execute(hierarchy_q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
    ref, quote, mv, sub = row

    # 2. Fetch Cached Signals
    cache_q = select(SignalCache).where(SignalCache.entity_id == sub.id)
    cache_records = (await db.execute(cache_q)).scalars().all()

    # 3. Fetch Existing Audits for this Model Version
    audit_q = select(SignalAuditRecord).where(SignalAuditRecord.model_version_id == mv.id)
    audit_records = {a.signal_id: a for a in (await db.execute(audit_q)).scalars().all()}

    signals = []
    for cache in cache_records:
        audit = audit_records.get(cache.signal_id)
        data = cache.data or {}
        
        is_flagged = data.get("is_flagged", False)
        if not include_all and not is_flagged and not audit:
            continue

        inferred = float(cache.inferred_value if cache.inferred_value is not None else data.get("value", 0))
        audited = float(audit.audited_value) if audit and audit.audited_value is not None else None

        signals.append(ReferralSignalDetail(
            signal_id=cache.signal_id,
            signal_name=data.get("name", cache.signal_id),
            group_id=data.get("group_id", "general"),
            group_name=data.get("group_name", "General"),
            inferred_value=inferred,
            audited_value=audited,
            is_overridden=bool(audit and audit.is_overridden),
            weight=float(data.get("weight", 0.1)),
            contribution_to_score=float(data.get("contribution", 0.0)),
            is_flagged=is_flagged,
            flag_reason=data.get("flag_reason"),
            confidence=cache.confidence or 1.0,
            data_sources=data.get("sources", []),
            extracted_at=cache.extracted_at
        ))

    return ReferralSignalsResponse(
        referral_id=referral_id,
        model_version_id=mv.version_id,
        signals=signals,
        flagged_count=sum(1 for s in signals if s.is_flagged),
        overridden_count=sum(1 for s in signals if s.is_overridden),
        total_signals=len(cache_records),
        signal_coverage=1.0,
        average_confidence=sum(s.confidence for s in signals)/len(signals) if signals else 1.0
    )


@router.post("/referrals/{referral_id}/signals/override", response_model=SignalOverrideResponse)
async def override_signal(
    referral_id: str,
    override: SignalOverrideRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Execute a Phase 8 Signal Override.
    Underwriters audit inputs, not outputs. Creates a v2+ Model Version.
    """
    # 1. Fetch Hierarchy
    hierarchy_q = select(Referral, Quote, ModelVersionRecord, Submission).join(
        Quote, Referral.quote_id == Quote.id
    ).join(
        ModelVersionRecord, Quote.model_version_id == ModelVersionRecord.id
    ).join(
        Submission, Quote.submission_id == Submission.id
    ).where(Referral.referral_id == referral_id)
    
    row = (await db.execute(hierarchy_q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")
    ref, quote, mv, sub = row

    # 2. Fetch the specific Signal
    cache_q = select(SignalCache).where(
        and_(SignalCache.entity_id == sub.submission_id, SignalCache.signal_id == override.signal_id)
    ).order_by(SignalCache.extracted_at.desc()).limit(1)
    
    cache = (await db.execute(cache_q)).scalar_one_or_none()
    if not cache:
        raise HTTPException(status_code=404, detail=f"Signal '{override.signal_id}' not found")

    inferred = float(cache.inferred_value if cache.inferred_value is not None else (cache.data or {}).get("value", 0))

    # 3. Create the NEW Model Version (v2+)
    new_score = (mv.pure_composite_score or 500) + ((override.audited_value - inferred) * 0.5) # Simplified proxy score impact
    new_tier = max(1, min(5, int(5 - (new_score / 200)))) # Simplified tier formula
    tier_labels = {1: "PREFERRED", 2: "STANDARD", 3: "STANDARD_PLUS", 4: "ELEVATED", 5: "HIGH_RISK"}
    
    new_mv = ModelVersionRecord(
        version_id=generate_id("mv"),
        submission_id=sub.id,
        version_number=(mv.version_number or 1) + 1,
        version_type="signal_override",
        is_latest=True,
        config_hash=mv.config_hash,
        coverage=mv.coverage,
        pure_composite_score=new_score,
        final_tier=new_tier,
        tier_label=tier_labels.get(new_tier, "STANDARD"),
        decision=mv.decision,
        created_by=override.underwriter_id or "system",
        created_at=datetime.utcnow()
    )
    
    # Deprecate the old one
    mv.is_latest = False
    db.add(new_mv)
    await db.flush() # Yields new_mv.id

    # 4. Create the Audit Record
    audit = SignalAuditRecord(
        signal_cache_id=cache.id,
        model_version_id=new_mv.id,
        signal_id=override.signal_id,
        entity_id=sub.submission_id,
        inferred_value={"value": inferred},
        audited_value={"value": override.audited_value},
        is_overridden=True,
        overridden_by=safe_uuid(override.underwriter_id),
        overridden_at=datetime.utcnow(),
        override_rationale=override.rationale,
        evidence_reference=override.evidence_reference,
        score_impact=new_score - (mv.pure_composite_score or 0),
        tier_impact=new_tier - (mv.final_tier or 0)
    )
    db.add(audit)

    # 5. Point the Quote to the new, corrected Model Version
    quote.model_version_id = new_mv.id

    await db.commit()

    return SignalOverrideResponse(
        signal_id=override.signal_id,
        entity_id=sub.submission_id,
        model_version_id=new_mv.version_id,
        inferred_value=inferred,
        audited_value=override.audited_value,
        score_impact=audit.score_impact,
        tier_impact=audit.tier_impact,
        new_composite_score=new_score,
        new_tier=new_tier,
        new_tier_label=new_mv.tier_label,
        overridden_by=override.underwriter_id or "system",
        overridden_at=audit.overridden_at,
        override_rationale=override.rationale,
        evidence_reference=override.evidence_reference,
        previous_model_version=mv.version_id,
        new_model_version=new_mv.version_id,
    )


# =============================================================================
# STATS & UTILITIES
# =============================================================================

@router.get("/referrals/pending/count")
async def get_pending_count(db: AsyncSession = Depends(get_async_db)):
    """Get real-time count of pending referrals from DB."""
    query = select(func.count(Referral.id), func.min(Referral.created_at)).where(
        Referral.status == ReferralStatus.PENDING
    )
    result = (await db.execute(query)).first()
    
    count = result[0] or 0
    oldest = result[1]
    oldest_hours = (datetime.now(timezone.utc) - oldest.replace(tzinfo=timezone.utc)).total_seconds() / 3600 if oldest else 0
    
    return {
        "pending_count": count,
        "oldest_hours": round(oldest_hours, 1)
    }

@router.get("/referrals/stats")
async def get_referral_stats(db: AsyncSession = Depends(get_async_db)):
    """Aggregate referral DB statistics."""
    query = select(Referral.status, func.count(Referral.id)).group_by(Referral.status)
    rows = (await db.execute(query)).all()
    
    stats = {"pending": 0, "approved": 0, "declined": 0, "modified": 0, "in_review": 0}
    total = 0
    
    for status_enum, count in rows:
        stats[status_enum.value] = count
        total += count
        
    resolved = stats["approved"] + stats["declined"] + stats["modified"]
    
    return {
        "total": total,
        "pending": stats["pending"] + stats["in_review"],
        "approved": stats["approved"] + stats["modified"],
        "declined": stats["declined"],
        "approval_rate": round((stats["approved"] + stats["modified"]) / resolved, 2) if resolved > 0 else 0.0,
        "avg_resolution_hours": 0.0 # Placeholder for advanced DB date math
    }