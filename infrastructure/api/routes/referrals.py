"""
DSI Referral Endpoints (Phase 8/11)

Endpoints for managing underwriter referrals and signal overrides.
Wired to database repositories (Phase 8).

Phase 8: Deterministic Referral Management
- Underwriters audit inputs (signals), not outputs (premiums)
- Signal overrides preserve inferred_value, set audited_value
- Model versioning on override (v1=machine, v2+=audited)
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..types import (
    ReferralDecision,
    ReferralDecisionType,
    ReferralDetail,
    ReferralListItem,
    QuoteResponse,
    QuoteStatus as APIQuoteStatus,
    SignalOverrideRequest,
    SignalOverrideResponse,
    ReferralSignalDetail,
    ReferralSignalsResponse,
    ModelVersionResponse,
    DiscoverySummary,
    SignalSummary,
    LossPropensitySummary,
    ExposureSummary,
)
from ...db.config import get_async_db
from ...db.models import (
    Referral,
    Quote,
    Submission,
    ModelVersionRecord,
    SignalCache,
    ReferralStatus,
    QuoteStatus as DBQuoteStatus,
)
from ...db.repositories import (
    ReferralRepository,
    QuoteRepository,
    ModelVersionRepository,
    SignalCacheRepository,
    SignalAuditRepository,
    AuditLogRepository,
)


logger = logging.getLogger("dsi.api.referrals")

router = APIRouter()


# =============================================================================
# REQUEST MODELS
# =============================================================================

class AssignRequest(BaseModel):
    """Request to assign a referral to an underwriter."""
    underwriter_id: str = Field(..., description="UUID of the underwriter")


# =============================================================================
# CONSTANTS
# =============================================================================

_TIER_LABELS = {
    1: "PREFERRED",
    2: "STANDARD",
    3: "STANDARD_PLUS",
    4: "ELEVATED",
    5: "HIGH_RISK",
}

_TIER_BANDS = [(800, 1), (650, 2), (500, 3), (350, 4), (0, 5)]

# Fields copied verbatim from one ModelVersionRecord to the next when creating
# a new version (signal_override or referral_adjustment).
_MV_COPY_FIELDS = [
    "config_hash", "coverage", "configuration_name",
    "discovery_output", "signal_outputs", "categorical_outputs", "group_scores",
    "pure_composite_score", "confidence", "signal_coverage",
    "signal_conditions", "query_conditions",
    "tier_overrides", "score_based_tier", "final_tier", "tier_label",
    "base_premium", "base_premium_method", "modifiers_applied",
    "premium_after_modifiers", "limit_premiums", "final_premium",
    "decision", "auto_approve", "referral_reasons", "notes",
    # Loss propensity
    "loss_propensity_score", "severity_propensity_score",
    "loss_propensity_band", "severity_propensity_band",
    "loss_confidence", "loss_cohort_id", "loss_cohort_name",
    "loss_cohort_confidence", "loss_frequency_multiplier",
    "loss_severity_multiplier", "loss_combined_modifier",
    "loss_trend_direction", "loss_previous_score",
    "loss_score_velocity", "loss_last_refresh",
    "correlation_matrix_version",
    # Exposure
    "exposure_value", "exposure_band_id", "exposure_band_label",
    "exposure_magnitude_score", "exposure_modifier",
    "exposure_assessment_method",
]


# =============================================================================
# HELPERS
# =============================================================================

def _parse_uuid(value: str, field_name: str = "ID") -> uuid.UUID:
    """Parse a string as UUID, raising HTTPException on failure."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}: must be a valid UUID",
        )


def _extract_signal_value(jsonb_value) -> Optional[float]:
    """Extract a numeric score from a JSONB signal value."""
    if jsonb_value is None:
        return None
    if isinstance(jsonb_value, (int, float)):
        return float(jsonb_value)
    if isinstance(jsonb_value, dict):
        for key in ("value", "score"):
            if key in jsonb_value:
                return float(jsonb_value[key])
    return None


def _score_to_tier(composite: float) -> tuple:
    """Determine (tier, tier_label) from a 0-1000 composite score."""
    for threshold, tier in _TIER_BANDS:
        if composite >= threshold:
            return tier, _TIER_LABELS[tier]
    return 5, _TIER_LABELS[5]


def _recalculate_score(signals: List[SignalCache]) -> tuple:
    """
    Recalculate composite score and tier from signal cache entries.
    Returns (composite_score, tier, tier_label).
    """
    if not signals:
        return 0.0, 5, "HIGH_RISK"

    total = 0.0
    for sig in signals:
        # Use audited_value if overridden, else inferred_value
        if sig.is_overridden and sig.audited_value is not None:
            value = _extract_signal_value(sig.audited_value)
        else:
            value = _extract_signal_value(sig.inferred_value)

        if value is None:
            raw = sig.data.get("value") if isinstance(sig.data, dict) else None
            value = _extract_signal_value(raw) if raw is not None else 50.0

        weight = 1.0 / len(signals)
        if isinstance(sig.data, dict) and "weight" in sig.data:
            weight = float(sig.data["weight"])

        total += value * weight * 10  # 0-1000 scale

    tier, tier_label = _score_to_tier(total)
    return total, tier, tier_label


def _copy_mv_fields(source: ModelVersionRecord) -> Dict[str, Any]:
    """Copy transferable fields from an existing ModelVersionRecord."""
    return {f: getattr(source, f) for f in _MV_COPY_FIELDS}


async def _load_referral_context(db: AsyncSession, referral_id: str):
    """
    Load a referral with all related data for detail responses.
    Returns (referral, quote, submission, initial_model_version).
    Raises 404 if not found.
    """
    result = await db.execute(
        select(Referral)
        .where(Referral.referral_id == referral_id)
        .options(
            selectinload(Referral.quote)
            .selectinload(Quote.submission),
            selectinload(Referral.quote)
            .selectinload(Quote.model_version),
        )
    )
    referral = result.scalar_one_or_none()

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    quote = referral.quote
    submission = quote.submission

    # Get initial model version (v1) for original scoring data
    mv_result = await db.execute(
        select(ModelVersionRecord)
        .where(ModelVersionRecord.submission_id == quote.submission_id)
        .order_by(ModelVersionRecord.version_number)
        .limit(1)
    )
    initial_mv = mv_result.scalar_one_or_none()

    return referral, quote, submission, initial_mv


def _build_referral_detail(
    referral: Referral,
    quote: Quote,
    submission: Submission,
    initial_mv: Optional[ModelVersionRecord],
) -> ReferralDetail:
    """Build ReferralDetail response from DB models."""
    return ReferralDetail(
        referral_id=referral.referral_id,
        quote_id=quote.quote_id,
        submission_id=submission.submission_id,
        entity_name=submission.entity_name,
        coverage=submission.coverage,
        status=referral.status.value,
        reasons=referral.reasons or [],
        original_tier=initial_mv.final_tier if initial_mv else 0,
        original_score=int(initial_mv.pure_composite_score or 0) if initial_mv else 0,
        original_premium=quote.recommended_premium or 0,
        resolved_at=referral.reviewed_at,
        resolved_by=str(referral.reviewed_by) if referral.reviewed_by else None,
        resolution_notes=[referral.review_notes] if referral.review_notes else [],
        tier_override=referral.tier_override,
        premium_adjustment=referral.premium_adjustment,
        created_at=referral.created_at,
    )


def _build_quote_from_referral(
    referral: Referral,
    quote: Quote,
    submission: Submission,
    mv: ModelVersionRecord,
) -> QuoteResponse:
    """Build a QuoteResponse in the context of a referral."""
    # Determine effective API status based on referral state
    if referral.status in (ReferralStatus.PENDING, ReferralStatus.IN_REVIEW):
        api_status = APIQuoteStatus.REFERRED
    elif referral.status in (ReferralStatus.APPROVED, ReferralStatus.MODIFIED):
        api_status = APIQuoteStatus.READY
    elif referral.status == ReferralStatus.DECLINED:
        api_status = APIQuoteStatus.DECLINED
    else:
        api_status = APIQuoteStatus.REFERRED

    discovery = None
    if mv.discovery_output and isinstance(mv.discovery_output, dict):
        discovery = DiscoverySummary(
            domain=mv.discovery_output.get("domain", "unknown"),
            confidence=mv.discovery_output.get("confidence", "low"),
            industry=mv.discovery_output.get("industry"),
            employee_count=mv.discovery_output.get("employee_count"),
        )

    return QuoteResponse(
        quote_id=quote.quote_id,
        submission_id=submission.submission_id,
        status=api_status,
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
        referral_reasons=mv.referral_reasons or [],
        referral_id=referral.referral_id if referral.status in (
            ReferralStatus.PENDING, ReferralStatus.IN_REVIEW,
        ) else None,
        valid_until=quote.valid_until,
        created_at=quote.created_at,
        discovery=discovery,
    )


# =============================================================================
# ENDPOINTS — static paths first to avoid {referral_id} capture
# =============================================================================

@router.get("/referrals/pending/count")
async def get_pending_count(db: AsyncSession = Depends(get_async_db)):
    """
    Get count of pending referrals.
    """
    result = await db.execute(
        select(func.count(Referral.id))
        .where(Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.IN_REVIEW]))
    )
    pending_count = result.scalar() or 0

    oldest_result = await db.execute(
        select(func.min(Referral.created_at))
        .where(Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.IN_REVIEW]))
    )
    oldest_created = oldest_result.scalar()
    oldest_hours = 0.0
    if oldest_created:
        oldest_hours = (datetime.utcnow() - oldest_created).total_seconds() / 3600

    return {
        "pending_count": pending_count,
        "oldest_hours": round(oldest_hours, 1),
    }


@router.get("/referrals/stats")
async def get_referral_stats(db: AsyncSession = Depends(get_async_db)):
    """
    Get referral statistics.
    """
    total_result = await db.execute(select(func.count(Referral.id)))
    total = total_result.scalar() or 0

    if total == 0:
        return {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "declined": 0,
            "approval_rate": 0.0,
            "avg_resolution_hours": 0.0,
        }

    pending_result = await db.execute(
        select(func.count(Referral.id))
        .where(Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.IN_REVIEW]))
    )
    pending = pending_result.scalar() or 0

    approved_result = await db.execute(
        select(func.count(Referral.id))
        .where(Referral.status.in_([ReferralStatus.APPROVED, ReferralStatus.MODIFIED]))
    )
    approved = approved_result.scalar() or 0

    declined_result = await db.execute(
        select(func.count(Referral.id))
        .where(Referral.status == ReferralStatus.DECLINED)
    )
    declined = declined_result.scalar() or 0
    resolved = approved + declined

    avg_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", Referral.reviewed_at - Referral.created_at) / 3600
            )
        )
        .where(Referral.reviewed_at.isnot(None))
    )
    avg_resolution = avg_result.scalar() or 0.0

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "declined": declined,
        "approval_rate": approved / resolved if resolved > 0 else 0.0,
        "avg_resolution_hours": round(float(avg_resolution), 1),
    }


# =============================================================================
# REFERRAL CRUD
# =============================================================================

@router.get("/referrals", response_model=List[ReferralListItem])
async def list_referrals(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, declined)"),
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List referrals with optional filtering.
    """
    query = (
        select(Referral)
        .join(Referral.quote)
        .join(Quote.submission)
        .options(
            selectinload(Referral.quote).selectinload(Quote.submission),
        )
    )

    if status:
        status_map = {
            "pending": [ReferralStatus.PENDING],
            "in_review": [ReferralStatus.IN_REVIEW],
            "approved": [ReferralStatus.APPROVED, ReferralStatus.MODIFIED],
            "declined": [ReferralStatus.DECLINED],
        }
        statuses = status_map.get(status, [])
        if statuses:
            query = query.where(Referral.status.in_(statuses))

    if coverage:
        query = query.where(Submission.coverage == coverage)

    query = query.order_by(Referral.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    referrals = list(result.scalars().all())

    return [
        ReferralListItem(
            referral_id=r.referral_id,
            entity_name=r.quote.submission.entity_name,
            coverage=r.quote.submission.coverage,
            status=r.status.value,
            reasons=r.reasons or [],
            age_hours=(datetime.utcnow() - r.created_at).total_seconds() / 3600,
            created_at=r.created_at,
        )
        for r in referrals
    ]


@router.get("/referrals/{referral_id}", response_model=ReferralDetail)
async def get_referral(
    referral_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get referral details by ID.
    """
    referral, quote, submission, initial_mv = await _load_referral_context(db, referral_id)
    return _build_referral_detail(referral, quote, submission, initial_mv)


@router.post("/referrals/{referral_id}/assign", response_model=ReferralDetail)
async def assign_referral(
    referral_id: str,
    body: AssignRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Assign a referral to an underwriter.

    Transitions the referral from PENDING to IN_REVIEW and records
    the responsible underwriter.  Returns 409 if already assigned to
    someone else; 400 if already resolved.
    """
    underwriter_uuid = _parse_uuid(body.underwriter_id, "underwriter_id")

    repo = ReferralRepository(db)
    referral = await repo.get_by_id(referral_id)

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status in (
        ReferralStatus.APPROVED, ReferralStatus.DECLINED, ReferralStatus.MODIFIED,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Referral already resolved with status: {referral.status.value}",
        )

    if (
        referral.status == ReferralStatus.IN_REVIEW
        and referral.assigned_to is not None
        and referral.assigned_to != underwriter_uuid
    ):
        raise HTTPException(
            status_code=409,
            detail="Referral already assigned to another underwriter",
        )

    await repo.assign(referral_id, assigned_to=underwriter_uuid)

    # Audit log
    audit_repo = AuditLogRepository(db)
    await audit_repo.log(
        event_type="referral",
        event_action="assign",
        resource_type="referral",
        resource_id=referral_id,
        user_id=underwriter_uuid,
        details={"assigned_to": str(underwriter_uuid)},
    )

    # Reload with full context for response
    referral, quote, submission, initial_mv = await _load_referral_context(db, referral_id)
    return _build_referral_detail(referral, quote, submission, initial_mv)


@router.patch("/referrals/{referral_id}", response_model=ReferralDetail)
async def process_referral(
    referral_id: str,
    decision: ReferralDecision,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Process a referral decision.

    Allows underwriters to approve, decline, or modify the quote.
    When adjustments are present, a new ModelVersionRecord is created
    so the full audit trail is preserved.
    """
    referral_repo = ReferralRepository(db)
    referral = await referral_repo.get_by_id(referral_id)

    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if referral.status in (
        ReferralStatus.APPROVED, ReferralStatus.DECLINED, ReferralStatus.MODIFIED,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Referral already resolved with status: {referral.status.value}",
        )

    reviewer_uuid = (
        _parse_uuid(decision.underwriter_id, "underwriter_id")
        if decision.underwriter_id
        else uuid.uuid4()
    )

    tier_override = None
    premium_adjustment = None
    if decision.adjustments:
        tier_override = decision.adjustments.get("tier_override")
        premium_adjustment = decision.adjustments.get("premium_adjustment")

    # 1. Persist decision and adjustments on referral row
    await referral_repo.review(
        referral_id=referral_id,
        reviewed_by=reviewer_uuid,
        decision=decision.decision.value,
        notes="; ".join(decision.notes) if decision.notes else None,
        tier_override=tier_override,
        premium_adjustment=premium_adjustment,
    )

    # Load quote (via FK UUID)
    quote_result = await db.execute(
        select(Quote)
        .where(Quote.id == referral.quote_id)
        .options(selectinload(Quote.submission))
    )
    quote = quote_result.scalar_one_or_none()

    if quote:
        quote_repo = QuoteRepository(db)

        # 2. If tier_override or premium_adjustment, create new ModelVersionRecord
        if tier_override is not None or premium_adjustment is not None:
            mv_repo = ModelVersionRepository(db)
            current_mv = await mv_repo.get_latest(quote.submission_id)

            if current_mv:
                mv_fields = _copy_mv_fields(current_mv)

                # Apply overrides
                if tier_override is not None:
                    mv_fields["final_tier"] = tier_override
                    mv_fields["tier_label"] = _TIER_LABELS.get(tier_override, "UNKNOWN")

                effective_premium = current_mv.final_premium or quote.recommended_premium or 0
                if premium_adjustment is not None:
                    mv_fields["final_premium"] = effective_premium * premium_adjustment
                    mv_fields["premium_after_modifiers"] = effective_premium * premium_adjustment

                mv_fields["auto_approve"] = False
                mv_fields["created_by"] = str(reviewer_uuid)
                mv_fields["notes"] = (current_mv.notes or []) + [
                    f"Referral adjustment by {reviewer_uuid}: "
                    f"tier_override={tier_override}, premium_adjustment={premium_adjustment}"
                ]

                new_mv = await mv_repo.create(
                    submission_id=quote.submission_id,
                    version_type="referral_adjustment",
                    **mv_fields,
                )

                # Point quote at new model version
                await quote_repo.update_model_version_id(quote.quote_id, new_mv.id)

        # 3. Update quote status based on decision
        if decision.decision in (ReferralDecisionType.APPROVE, ReferralDecisionType.MODIFY):
            await quote_repo.update_status(quote.quote_id, DBQuoteStatus.READY)
        elif decision.decision == ReferralDecisionType.DECLINE:
            await quote_repo.update_status(quote.quote_id, DBQuoteStatus.DECLINED)

    # 4. Audit log
    audit_repo = AuditLogRepository(db)
    await audit_repo.log(
        event_type="referral",
        event_action="review",
        resource_type="referral",
        resource_id=referral_id,
        user_id=reviewer_uuid,
        details={
            "decision": decision.decision.value,
            "tier_override": tier_override,
            "premium_adjustment": premium_adjustment,
        },
    )

    logger.info(
        f"Referral {referral_id} {decision.decision.value} by {reviewer_uuid}"
    )

    # Reload for response
    referral, quote, submission, initial_mv = await _load_referral_context(db, referral_id)
    return _build_referral_detail(referral, quote, submission, initial_mv)


@router.get("/referrals/{referral_id}/quote", response_model=QuoteResponse)
async def get_referral_quote(
    referral_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get the quote associated with a referral.
    """
    referral, quote, submission, _initial_mv = await _load_referral_context(db, referral_id)
    mv = quote.model_version  # current (latest) model version linked to the quote
    return _build_quote_from_referral(referral, quote, submission, mv)


# =============================================================================
# PHASE 8: SIGNAL OVERRIDE ENDPOINTS (Deterministic Referral Management)
# =============================================================================

@router.get("/referrals/{referral_id}/signals", response_model=ReferralSignalsResponse)
async def get_referral_signals(
    referral_id: str,
    include_all: bool = Query(False, description="Include all signals, not just flagged"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get signals for a referral (Phase 8: Underwriter Signal Review).

    Returns all signals with their inferred values, allowing underwriters
    to review and potentially override machine-inferred values.
    """
    referral, quote, submission, _initial_mv = await _load_referral_context(db, referral_id)

    entity_id = submission.submission_id
    signal_repo = SignalCacheRepository(db)
    signals = await signal_repo.get_entity_signals(entity_id, include_expired=True)

    detail_list: List[ReferralSignalDetail] = []
    flagged_count = 0
    overridden_count = 0

    for sig in signals:
        data = sig.data if isinstance(sig.data, dict) else {}

        is_flagged = data.get("is_flagged", False)
        is_overridden = sig.is_overridden or False

        if is_flagged:
            flagged_count += 1
        if is_overridden:
            overridden_count += 1

        if not include_all and not is_flagged:
            continue

        inferred = _extract_signal_value(sig.inferred_value) or _extract_signal_value(data.get("value")) or 50.0
        audited = _extract_signal_value(sig.audited_value) if is_overridden else None
        weight = float(data.get("weight", 1.0 / max(len(signals), 1)))
        effective = audited if is_overridden and audited is not None else inferred

        detail_list.append(ReferralSignalDetail(
            signal_id=sig.signal_id,
            signal_name=data.get("signal_name", sig.signal_id),
            group_id=data.get("group_id", "unknown"),
            group_name=data.get("group_name", "Unknown"),
            inferred_value=inferred,
            audited_value=audited,
            is_overridden=is_overridden,
            weight=weight,
            contribution_to_score=effective * weight * 10,
            is_flagged=is_flagged,
            flag_reason=data.get("flag_reason"),
            confidence=sig.confidence or data.get("confidence", 0.0),
            data_sources=data.get("data_sources", [sig.source_name]),
            extracted_at=sig.extracted_at or datetime.utcnow(),
        ))

    mv = quote.model_version
    avg_confidence = (
        sum(s.confidence for s in detail_list) / len(detail_list)
        if detail_list else 0.0
    )

    return ReferralSignalsResponse(
        referral_id=referral_id,
        model_version_id=mv.version_id if mv else "unknown",
        signals=detail_list,
        flagged_count=flagged_count,
        overridden_count=overridden_count,
        total_signals=len(signals),
        signal_coverage=1.0 if signals else 0.0,
        average_confidence=avg_confidence,
    )


@router.post("/referrals/{referral_id}/signals/override", response_model=SignalOverrideResponse)
async def override_signal(
    referral_id: str,
    override: SignalOverrideRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Override a signal value during referral review (Phase 8).

    This is the core Phase 8 operation: underwriters audit inputs (signals),
    not outputs (premiums). The formula remains pure.

    - inferred_value is PRESERVED (permanent machine view)
    - audited_value is SET (mutable human override)
    - A new model version is created (v1=machine, v2+=audited)
    - Score is recalculated using audited_value
    """
    # 1. Load referral → quote → submission_id, model_version_id
    referral, quote, submission, _initial_mv = await _load_referral_context(db, referral_id)
    entity_id = submission.submission_id

    # 2. Load signal from SignalCacheRepository
    signal_repo = SignalCacheRepository(db)
    signal_entry = await signal_repo.get_valid_cached(entity_id, override.signal_id)

    if not signal_entry:
        # Fall back to include expired signals (referral review may occur after TTL)
        all_signals = await signal_repo.get_entity_signals(entity_id, include_expired=True)
        signal_entry = next((s for s in all_signals if s.signal_id == override.signal_id), None)

    if not signal_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Signal '{override.signal_id}' not found for this entity",
        )

    # 3. Preserve inferred_value (read for audit record)
    old_inferred = _extract_signal_value(signal_entry.inferred_value) or 50.0

    # Store previous effective value for impact calculation
    old_effective = (
        _extract_signal_value(signal_entry.audited_value)
        if signal_entry.is_overridden
        else old_inferred
    )

    # Load all signals before the update (for score recalculation)
    all_signals = await signal_repo.get_entity_signals(entity_id, include_expired=True)

    # Get old composite score from current model version
    mv_repo = ModelVersionRepository(db)
    current_mv = await mv_repo.get_latest(quote.submission_id)
    old_composite = float(current_mv.pure_composite_score or 0) if current_mv else 0.0
    old_tier = (current_mv.final_tier or 5) if current_mv else 5

    # 4. Set audited_value and is_overridden on signal cache entry
    await db.execute(
        update(SignalCache)
        .where(SignalCache.id == signal_entry.id)
        .values(
            audited_value={"value": override.audited_value},
            is_overridden=True,
        )
    )
    await db.flush()

    # Refresh all_signals with the update applied (update the in-memory copy)
    for sig in all_signals:
        if sig.id == signal_entry.id:
            sig.audited_value = {"value": override.audited_value}
            sig.is_overridden = True

    # 5. Recalculate composite score and tier using all signals
    new_composite, new_tier, new_tier_label = _recalculate_score(all_signals)

    # 6. Create new ModelVersionRecord
    if current_mv:
        mv_fields = _copy_mv_fields(current_mv)
    else:
        mv_fields = {}

    underwriter_id = override.underwriter_id or "unknown"
    score_impact = new_composite - old_composite
    tier_impact = new_tier - old_tier

    mv_fields["pure_composite_score"] = new_composite
    mv_fields["final_tier"] = new_tier
    mv_fields["tier_label"] = new_tier_label
    mv_fields["score_based_tier"] = new_tier
    mv_fields["created_by"] = underwriter_id
    mv_fields["notes"] = (mv_fields.get("notes") or []) + [
        f"Signal '{override.signal_id}' overridden: "
        f"{old_inferred:.0f} -> {override.audited_value:.0f}"
    ]

    new_mv = await mv_repo.create(
        submission_id=quote.submission_id,
        version_type="signal_override",
        **mv_fields,
    )

    # 7. Create SignalAuditRecord (immutable audit trail)
    audit_repo = SignalAuditRepository(db)
    underwriter_uuid = _parse_uuid(underwriter_id, "underwriter_id") if underwriter_id != "unknown" else None
    await audit_repo.create_override(
        signal_cache_id=signal_entry.id,
        model_version_id=new_mv.id,
        signal_id=override.signal_id,
        entity_id=entity_id,
        inferred_value={"value": old_inferred},
        audited_value={"value": override.audited_value},
        overridden_by=underwriter_uuid or uuid.uuid4(),
        rationale=override.rationale,
        evidence_reference=override.evidence_reference,
        score_impact=score_impact,
        tier_impact=tier_impact,
    )

    # 8. Update quote.model_version_id to point to the new model version
    quote_repo = QuoteRepository(db)
    await quote_repo.update_model_version_id(quote.quote_id, new_mv.id)

    # Audit log
    general_audit = AuditLogRepository(db)
    await general_audit.log(
        event_type="signal",
        event_action="override",
        resource_type="signal_cache",
        resource_id=override.signal_id,
        details={
            "referral_id": referral_id,
            "entity_id": entity_id,
            "inferred_value": old_inferred,
            "audited_value": override.audited_value,
            "score_impact": score_impact,
            "tier_impact": tier_impact,
            "new_model_version": new_mv.version_id,
        },
    )

    now = datetime.utcnow()
    logger.info(
        f"Signal override on referral {referral_id}: "
        f"{override.signal_id} {old_inferred:.0f} -> {override.audited_value:.0f}, "
        f"score impact: {score_impact:+.0f}, tier impact: {tier_impact:+d}"
    )

    # 9. Return response
    return SignalOverrideResponse(
        signal_id=override.signal_id,
        entity_id=entity_id,
        model_version_id=new_mv.version_id,
        inferred_value=old_inferred,
        audited_value=override.audited_value,
        score_impact=score_impact,
        tier_impact=tier_impact,
        new_composite_score=new_composite,
        new_tier=new_tier,
        new_tier_label=new_tier_label,
        overridden_by=underwriter_id,
        overridden_at=now,
        rationale=override.rationale,
        evidence_reference=override.evidence_reference,
        previous_model_version=current_mv.version_id if current_mv else "unknown",
        new_model_version=new_mv.version_id,
    )


@router.delete("/referrals/{referral_id}/signals/{signal_id}/override")
async def revert_signal_override(
    referral_id: str,
    signal_id: str,
    underwriter_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revert a signal override back to machine-inferred value.

    Creates a new model version documenting the reversion and a
    SignalAuditRecord recording the revert.
    """
    referral, quote, submission, _initial_mv = await _load_referral_context(db, referral_id)
    entity_id = submission.submission_id

    # Find the signal
    signal_repo = SignalCacheRepository(db)
    all_signals = await signal_repo.get_entity_signals(entity_id, include_expired=True)
    signal_entry = next((s for s in all_signals if s.signal_id == signal_id), None)

    if not signal_entry:
        raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")

    if not signal_entry.is_overridden:
        raise HTTPException(status_code=400, detail=f"Signal '{signal_id}' is not overridden")

    # Store previous values for audit
    old_audited = _extract_signal_value(signal_entry.audited_value) or 0.0
    inferred = _extract_signal_value(signal_entry.inferred_value) or 50.0

    # Get old scores
    mv_repo = ModelVersionRepository(db)
    current_mv = await mv_repo.get_latest(quote.submission_id)
    old_composite = float(current_mv.pure_composite_score or 0) if current_mv else 0.0
    old_tier = (current_mv.final_tier or 5) if current_mv else 5

    # Revert the signal cache entry
    await db.execute(
        update(SignalCache)
        .where(SignalCache.id == signal_entry.id)
        .values(audited_value=None, is_overridden=False)
    )
    await db.flush()

    # Update in-memory copy for score recalculation
    for sig in all_signals:
        if sig.id == signal_entry.id:
            sig.audited_value = None
            sig.is_overridden = False

    # Recalculate score
    new_composite, new_tier, new_tier_label = _recalculate_score(all_signals)
    score_impact = new_composite - old_composite
    tier_impact = new_tier - old_tier

    # Create new model version documenting the reversion
    if current_mv:
        mv_fields = _copy_mv_fields(current_mv)
    else:
        mv_fields = {}

    revert_by = underwriter_id or "unknown"
    mv_fields["pure_composite_score"] = new_composite
    mv_fields["final_tier"] = new_tier
    mv_fields["tier_label"] = new_tier_label
    mv_fields["score_based_tier"] = new_tier
    mv_fields["created_by"] = revert_by
    mv_fields["notes"] = (mv_fields.get("notes") or []) + [
        f"Override reverted for '{signal_id}': {old_audited:.0f} -> {inferred:.0f} (machine)"
    ]

    new_mv = await mv_repo.create(
        submission_id=quote.submission_id,
        version_type="override_reverted",
        **mv_fields,
    )

    # Create audit record for the revert
    audit_repo = SignalAuditRepository(db)
    revert_uuid = _parse_uuid(revert_by, "underwriter_id") if revert_by != "unknown" else uuid.uuid4()
    await audit_repo.create_override(
        signal_cache_id=signal_entry.id,
        model_version_id=new_mv.id,
        signal_id=signal_id,
        entity_id=entity_id,
        inferred_value={"value": inferred},
        audited_value={"value": inferred},  # reverted to inferred
        overridden_by=revert_uuid,
        rationale=f"Override reverted — restoring machine-inferred value",
        score_impact=score_impact,
        tier_impact=tier_impact,
    )

    # Update quote model version
    quote_repo = QuoteRepository(db)
    await quote_repo.update_model_version_id(quote.quote_id, new_mv.id)

    # Audit log
    general_audit = AuditLogRepository(db)
    await general_audit.log(
        event_type="signal",
        event_action="revert_override",
        resource_type="signal_cache",
        resource_id=signal_id,
        details={
            "referral_id": referral_id,
            "reverted_from": old_audited,
            "reverted_to": inferred,
            "new_model_version": new_mv.version_id,
        },
    )

    logger.info(f"Signal override reverted on referral {referral_id}: {signal_id}")

    return {
        "status": "reverted",
        "signal_id": signal_id,
        "reverted_to": inferred,
        "new_composite_score": new_composite,
        "new_tier": new_tier,
        "new_model_version": new_mv.version_id,
    }


@router.get("/referrals/{referral_id}/model-versions", response_model=List[ModelVersionResponse])
async def get_model_versions(
    referral_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get model version history for a referral (Phase 8 audit trail).

    Shows the progression from v1 (machine view) through v2+ (audited views).
    """
    referral, quote, submission, _initial_mv = await _load_referral_context(db, referral_id)

    mv_repo = ModelVersionRepository(db)
    versions = await mv_repo.list_for_submission(quote.submission_id)

    return [
        ModelVersionResponse(
            version_id=mv.version_id,
            version_number=mv.version_number,
            version_type=mv.version_type or "initial",
            composite_score=mv.pure_composite_score or 0,
            tier=mv.final_tier or 0,
            tier_label=mv.tier_label or "UNKNOWN",
            confidence=mv.confidence or 0.0,
            signal_count=len(mv.signal_outputs) if isinstance(mv.signal_outputs, list) else 0,
            overridden_signals=[],  # populated from audit records if needed
            created_by=mv.created_by or "system",
            created_at=mv.created_at,
            notes=mv.notes or [],
        )
        for mv in versions
    ]
