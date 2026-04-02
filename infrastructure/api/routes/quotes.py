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
from sqlalchemy import select, update

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote,
    QuoteStatus,
    ModelVersionRecord,
    Referral,
    ReferralStatus,
    SubmissionNote,
)
from infrastructure.db.repositories import ModelVersionRepository

from ..utils import generate_id

from ..types import (
    QuoteRecord,
    LimitSelectionRequest,
    LimitSelectionResponse,
)

from infrastructure.api.routes.referrals import updateStatus_referral

from layers.risk.rol_recommender import ROLRecommender
from layers.risk.rol_validator import ROLValidator

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


@router.post("/quotes/{quote_code}/select-option", response_model=LimitSelectionResponse)
async def select_limit_option(
    quote_code: str,
    request: LimitSelectionRequest,
    db: AsyncSession = Depends(get_async_db),
) -> LimitSelectionResponse:
    """
    Select a limit/premium option and create a new model version.

    This is the mechanism for an underwriter to choose a specific limit from the
    ROL-driven options. It:
    1. Validates the selected limit exists in the pricing menu
    2. Creates a new model version (version_type="limit_selection")
    3. Sets final_premium and ROL columns to the selected option
    4. Updates the quote FK to the new version
    5. Recalculates the ROL recommendation around the selected limit

    All operations share the same database session and commit atomically.
    """

    # ── a. Resolve context ──────────────────────────────────────────────

    quote = (
        await db.execute(select(Quote).where(Quote.quote_code == quote_code))
    ).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status in (QuoteStatus.BOUND, QuoteStatus.EXPIRED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot select option on quote in status: {quote.status.value}",
        )

    old_model = (
        await db.execute(
            select(ModelVersionRecord).where(ModelVersionRecord.id == quote.model_version_id)
        )
    ).scalar_one_or_none()

    if not old_model:
        raise HTTPException(status_code=404, detail="Model version not found for quote")

    # ── b. Validate selected limit against pricing result ─────────────

    # Recompute limit_premiums from the pricer data stored on the model version
    # The pricer's scale_to_limits output is captured in the ROL columns;
    # we need to reconstruct the menu from the old model's pricing chain.
    # Since limit_premiums is no longer persisted, we reconstruct from the
    # base_premium_derivation and modifiers.  However, the simplest approach
    # is to use the ROL columns which already contain the limit/premium pairs.
    limit_premiums: Dict[str, float] = {}

    # Reconstruct from ROL columns (upper + lower are the recommended pair)
    if old_model.rol_upper_limit:
        limit_premiums[str(int(old_model.rol_upper_limit))] = old_model.rol_upper_premium or 0.0
    if old_model.rol_lower_limit:
        limit_premiums[str(int(old_model.rol_lower_limit))] = old_model.rol_lower_premium or 0.0

    # Also check the quote's recommended limit
    if quote.recommended_limit:
        rec_key = str(int(quote.recommended_limit))
        if rec_key not in limit_premiums and quote.recommended_premium:
            limit_premiums[rec_key] = quote.recommended_premium

    selected_key = str(request.selected_limit)
    if selected_key not in limit_premiums:
        available = list(limit_premiums.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Limit {request.selected_limit} not available. Options: {available}",
        )

    selected_premium = limit_premiums[selected_key]
    selected_rol = (selected_premium / request.selected_limit) if request.selected_limit > 0 else 0.0

    # ── c. Create new model version ───────────────────────────────────

    mv_repo = ModelVersionRepository(db)
    new_model = await mv_repo.create(
        submission_id=old_model.submission_id,
        version_type="limit_selection",
        config_hash=old_model.config_hash,
        coverage=old_model.coverage,
        configuration_name=old_model.configuration_name,
        categorical_outputs=old_model.categorical_outputs,
        signal_conditions=old_model.signal_conditions,
        query_conditions=old_model.query_conditions,
        tier_overrides=old_model.tier_overrides,
        modifiers_applied=old_model.modifiers_applied,
        referral_reasons=old_model.referral_reasons,
        # Scoring (carry forward)
        group_scores=old_model.group_scores,
        pure_composite_score=old_model.pure_composite_score,
        final_composite_score=old_model.final_composite_score,
        confidence=old_model.confidence,
        signal_coverage=old_model.signal_coverage,
        score_based_tier=old_model.score_based_tier,
        final_tier=old_model.final_tier,
        tier_label=old_model.tier_label,
        # Pricing — updated to selected option
        base_premium=old_model.base_premium,
        base_premium_method=old_model.base_premium_method,
        base_premium_derivation=old_model.base_premium_derivation,
        premium_after_modifiers=old_model.premium_after_modifiers,
        final_premium=selected_premium,
        uncapped_premium=old_model.uncapped_premium,
        # ILF audit (carry forward)
        ilf_factor=old_model.ilf_factor,
        ilf_method=old_model.ilf_method,
        ilf_anchor_limit=old_model.ilf_anchor_limit,
        # ROL — set to selected option
        rol_upper_limit=float(request.selected_limit),
        rol_upper_premium=selected_premium,
        rol_upper_rol=selected_rol,
        rol_upper_rationale=f"User-selected limit",
        rol_lower_limit=old_model.rol_lower_limit,
        rol_lower_premium=old_model.rol_lower_premium,
        rol_lower_rol=old_model.rol_lower_rol,
        rol_lower_rationale=old_model.rol_lower_rationale,
        # Decision (carry forward)
        decision=old_model.decision,
        auto_approve=old_model.auto_approve,
        # Loss propensity (carry forward)
        loss_propensity_score=old_model.loss_propensity_score,
        severity_propensity_score=old_model.severity_propensity_score,
        loss_propensity_band=old_model.loss_propensity_band,
        severity_propensity_band=old_model.severity_propensity_band,
        loss_confidence=old_model.loss_confidence,
        loss_cohort_code=old_model.loss_cohort_code,
        loss_cohort_name=old_model.loss_cohort_name,
        loss_cohort_confidence=old_model.loss_cohort_confidence,
        loss_frequency_multiplier=old_model.loss_frequency_multiplier,
        loss_severity_multiplier=old_model.loss_severity_multiplier,
        loss_combined_modifier=old_model.loss_combined_modifier,
        loss_trend_direction=old_model.loss_trend_direction,
        loss_previous_score=old_model.loss_previous_score,
        loss_score_velocity=old_model.loss_score_velocity,
        loss_last_refresh=old_model.loss_last_refresh,
        # Exposure (carry forward)
        exposure_value=old_model.exposure_value,
        exposure_band_id=old_model.exposure_band_id,
        exposure_band_label=old_model.exposure_band_label,
        exposure_size_score=old_model.exposure_size_score,
        exposure_modifier=old_model.exposure_modifier,
    )

    # ── c2. Record limit selection as submission notes ──────────────────
    limit_note = SubmissionNote(
        submission_id=old_model.submission_id,
        note=f"Limit selection: {request.selected_limit:,} @ ${selected_premium:,.2f} (ROL {selected_rol:.4f})",
        source="limit_selection",
    )
    db.add(limit_note)
    if request.rationale:
        rationale_note = SubmissionNote(
            submission_id=old_model.submission_id,
            note=request.rationale,
            source="underwriter",
        )
        db.add(rationale_note)

    # ── d. Update quote FK and premium ────────────────────────────────

    await db.execute(
        update(Quote)
        .where(Quote.quote_code == quote_code)
        .values(
            model_version_id=new_model.id,
            recommended_premium=selected_premium,
            recommended_limit=float(request.selected_limit),
            updated_at=datetime.now(timezone.utc),
        )
    )

    # Mark old version as not latest
    await db.execute(
        update(ModelVersionRecord)
        .where(ModelVersionRecord.id == old_model.id)
        .values(is_latest=False)
    )

    await db.commit()

    logger.info(
        f"Limit selection: {quote_code} → limit={request.selected_limit}, "
        f"premium={selected_premium:.2f}, ROL={selected_rol:.4f}, "
        f"version={new_model.version_code}"
    )

    decision_str = old_model.decision.value if old_model.decision else "refer"

    return LimitSelectionResponse(
        quote_code=quote_code,
        new_version_code=new_model.version_code,
        previous_version_code=old_model.version_code,
        selected_limit=request.selected_limit,
        selected_premium=selected_premium,
        selected_rol=round(selected_rol, 6),
        decision=decision_str,
        message=f"New version created with limit {request.selected_limit:,} at ${selected_premium:,.2f}",
    )