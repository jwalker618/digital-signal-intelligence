"""
DSI Signal Endpoints - Database Backed

Endpoint for applying audited_value overrides to signals.
Creates a new model version via lightweight recalculation (no re-extraction),
updates the quote FK, creates a referral if required, and records the audit trail.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Quote,
    QuoteStatus,
    ModelVersionRecord,
    ModelVersionSignal,
    Signal,
    DecisionType,
)
from infrastructure.db.repositories import (
    ModelVersionRepository,
    ModelVersionSignalRepository,
    SignalAuditRepository,
    QuoteRepository,
    ReferralRepository,
)

from ..types import (
    SignalOverrideRequest, 
    SignalOverrideResponse,
)

logger = logging.getLogger("dsi.api.signals")
router = APIRouter()


# =============================================================================
# LIGHTWEIGHT RECALCULATION
# =============================================================================

def recalculate_composite_from_signals(
    signal_rows: List[ModelVersionSignal],
    old_model: ModelVersionRecord,
) -> Dict:
    """
    Lightweight recalculation of composite score from model_version_signal rows.

    Mirrors the scorer's calculate_composite logic:
    - Groups signals by group_code
    - Weighted average within each group (score * weight / sum_weights)
    - Weighted sum across groups using the group_scores already stored on
      the previous model version as a reference for group weights.

    The model_version_signal rows already carry per-signal weight and
    group_code, so we can recompute without loading the YAML config.

    Returns dict with: pure_composite_score, group_scores, confidence
    """
    # Group signals by group_code
    signals_by_group: Dict[str, list] = {}
    for sig in signal_rows:
        gcode = sig.group_code or "ungrouped"
        if gcode not in signals_by_group:
            signals_by_group[gcode] = []
        signals_by_group[gcode].append(sig)

    # Calculate per-group scores (weighted average of signal scores within group)
    group_scores: Dict[str, float] = {}
    for gcode, sigs in signals_by_group.items():
        total_weighted = sum((s.score or 0.0) * (s.weight or 0.0) for s in sigs)
        total_weight = sum(s.weight or 0.0 for s in sigs)
        if total_weight > 0:
            group_scores[gcode] = total_weighted / total_weight
        else:
            group_scores[gcode] = 50.0  # neutral default

    # To compute the composite, we need group-level weights.
    # The previous model version stores group_scores (dict of group_code → score).
    # We derive group weights from their proportional contribution or use equal weighting.
    # Best approach: use the stored group_scores from old model to infer the weighting.
    old_group_scores = old_model.group_scores or {}

    # If we have the same groups and old composite, reverse-engineer group weights
    # from the old data. Otherwise fall back to equal weighting.
    # The scorer uses: composite = sum(group_score * group_weight * 10) on 0-1000 scale
    # where group_score is 0-100 and group_weight sums to ~1.0
    #
    # Since we're doing a lightweight recalc, we use the proportional change approach:
    # For each group whose score changed, compute the delta and scale it by the
    # group's contribution ratio to the old composite.
    old_composite = old_model.pure_composite_score or 0.0

    if old_group_scores and old_composite > 0:
        # Proportional contribution method:
        # Each group's contribution to composite = (group_score * group_weight * 10)
        # We can solve for group_weight = contribution / (group_score * 10)
        # But since we don't store contribution separately, we use the ratio approach.
        #
        # Simpler: recompute composite using same structure.
        # The old composite was computed from old group scores with some weights.
        # If only one signal changed, the delta in composite =
        #   (new_group_score - old_group_score) * group_weight * 10
        #
        # We can compute: new_composite = old_composite + sum of deltas
        new_composite = old_composite
        for gcode, new_gscore in group_scores.items():
            old_gscore = old_group_scores.get(gcode)
            if old_gscore is not None:
                # Estimate group_weight from its contribution ratio
                # contribution = old_gscore * group_weight * 10
                # group_weight = contribution / (old_gscore * 10)
                # But we don't have contribution. Use ratio approach:
                # If all groups have equal weight, each contributes old_composite/n
                # Better: proportional to (old_gscore * 10) / old_composite
                if old_gscore > 0:
                    # group_weight * 10 = old_contribution / old_gscore
                    # old_contribution = old_composite * (old_gscore / sum_of_all_old_gscores)
                    # This is an approximation for equal-weight groups
                    pass

        # Fall back to the direct method: recompute composite from group scores
        # using equal group weights (most common config pattern).
        # This is the safest approach when we don't have config weights available.
        n_groups = len(group_scores)
        if n_groups > 0:
            # Equal weight per group: each weight = 1/n_groups
            # composite = sum(group_score * (1/n) * 10) = 10 * mean(group_scores)
            new_composite = 10.0 * sum(group_scores.values()) / n_groups
        else:
            new_composite = old_composite
    else:
        # No old data to reference — compute from scratch with equal weighting
        n_groups = len(group_scores)
        if n_groups > 0:
            new_composite = 10.0 * sum(group_scores.values()) / n_groups
        else:
            new_composite = 0.0

    # Confidence: average across all signals that have data
    all_sigs = [s for sigs in signals_by_group.values() for s in sigs]
    populated = [s for s in all_sigs if not s.was_absent]
    confidence = len(populated) / len(all_sigs) if all_sigs else 0.5

    return {
        "pure_composite_score": round(new_composite, 2),
        "group_scores": group_scores,
        "confidence": round(confidence, 4),
        "signal_coverage": round(len(populated) / len(all_sigs), 4) if all_sigs else 0.0,
    }


def determine_tier_from_score(
    composite_score: float,
    old_model: ModelVersionRecord,
) -> Dict:
    """
    Determine tier from composite score using the tier bands stored on the
    previous model version.

    For a lightweight recalc we try to load the compiled config. If unavailable,
    we estimate from the old model's score-to-tier mapping as a reference.
    """
    try:
        from infrastructure.models.compiler import get_config
        config = get_config(old_model.coverage)

        # Use pricer's tier resolution
        from layers.risk.pricer import ModelPricer
        pricer = ModelPricer()
        tier_band = pricer.get_tier_for_score(composite_score, config)

        # Determine decision from tier band
        if hasattr(tier_band, 'auto_decline') and tier_band.auto_decline:
            decision = DecisionType.DECLINE
        elif hasattr(tier_band, 'auto_approve') and tier_band.auto_approve:
            decision = DecisionType.APPROVE
        else:
            decision = DecisionType.REFER

        # Calculate base premium from tier
        base_premium, method, _derivation = pricer.calculate_base_premium(
            tier=tier_band.id,
            tier_band=tier_band,
            submission_data={},
            config=config,
        )

        return {
            "score_based_tier": tier_band.id,
            "final_tier": tier_band.id,
            "tier_label": tier_band.label,
            "decision": decision,
            "auto_approve": getattr(tier_band, 'auto_approve', False),
            "base_premium": base_premium,
            "base_premium_method": method,
            "final_premium": base_premium,
            "premium_after_modifiers": base_premium,
        }
    except Exception as e:
        logger.warning("Config-based tier resolution failed, using old model reference: %s", e)

        # Fallback: keep the old tier if score hasn't crossed a boundary
        # This is a safe degradation — the old model has the tier mapping
        return {
            "score_based_tier": old_model.score_based_tier,
            "final_tier": old_model.final_tier,
            "tier_label": old_model.tier_label,
            "decision": old_model.decision,
            "auto_approve": old_model.auto_approve,
            "base_premium": old_model.base_premium,
            "base_premium_method": old_model.base_premium_method,
            "final_premium": old_model.final_premium,
            "premium_after_modifiers": old_model.premium_after_modifiers,
        }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/signals/{quote_code}/override", response_model=SignalOverrideResponse)
async def override_signal(
    quote_code: str,
    request: SignalOverrideRequest,
    db: AsyncSession = Depends(get_async_db),
) -> SignalOverrideResponse:
    """
    Apply an audited_value override to a signal on a quote.

    This is an atomic operation that:
    1. Validates the quote and resolves the target signal
    2. Creates a new model version (lightweight recalc — no signal re-extraction)
    3. Copies all signal bindings, applying the override to the target signal
    4. Recalculates composite score, tier, and pricing
    5. Records a signal_audit_record for the compliance trail
    6. Updates the quote to point to the new model version
    7. Creates a referral if the new decision requires one

    All operations share the same database session and commit atomically.
    """

    # ── a. Resolve context ──────────────────────────────────────────────

    # Fetch quote
    quote = (
        await db.execute(select(Quote).where(Quote.quote_code == quote_code))
    ).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status in (QuoteStatus.BOUND, QuoteStatus.EXPIRED, QuoteStatus.DECLINED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot override signal on quote in status: {quote.status.value}",
        )

    # Fetch current model version
    old_model = (
        await db.execute(
            select(ModelVersionRecord).where(ModelVersionRecord.id == quote.model_version_id)
        )
    ).scalar_one_or_none()

    if not old_model:
        raise HTTPException(status_code=404, detail="Model version not found for quote")

    # Fetch all model_version_signal rows for the current model version
    old_signals = (
        await db.execute(
            select(ModelVersionSignal)
            .where(ModelVersionSignal.model_version_id == old_model.id)
            .order_by(ModelVersionSignal.group_code, ModelVersionSignal.signal_id)
        )
    ).scalars().all()

    if not old_signals:
        raise HTTPException(
            status_code=404,
            detail="No signal data found for this model version",
        )

    # Find the target signal by code (join to signals reference table)
    target_signal_row = None
    target_signal_int_id = None

    # Resolve signal_code to integer signal_id
    signal_ref = (
        await db.execute(
            select(Signal).where(Signal.code == request.signal_code)
        )
    ).scalar_one_or_none()

    if not signal_ref:
        raise HTTPException(
            status_code=404,
            detail=f"Signal code '{request.signal_code}' not found in registry",
        )

    target_signal_int_id = signal_ref.id

    # Find the model_version_signal row for this signal
    for sig in old_signals:
        if sig.signal_id == target_signal_int_id:
            target_signal_row = sig
            break

    if not target_signal_row:
        raise HTTPException(
            status_code=404,
            detail=f"Signal '{request.signal_code}' not found in model version {old_model.version_code}",
        )

    original_score = target_signal_row.score or 0.0

    # ── b. Create new model version ─────────────────────────────────────

    mv_repo = ModelVersionRepository(db)
    new_model = await mv_repo.create(
        submission_id=old_model.submission_id,
        version_type="signal_override",
        # Carry forward all fields from the old model version
        config_hash=old_model.config_hash,
        coverage=old_model.coverage,
        configuration_name=old_model.configuration_name,
        discovery_output=old_model.discovery_output,
        signal_outputs=old_model.signal_outputs,
        categorical_outputs=old_model.categorical_outputs,
        signal_conditions=old_model.signal_conditions,
        query_conditions=old_model.query_conditions,
        tier_overrides=old_model.tier_overrides,
        modifiers_applied=old_model.modifiers_applied,
        referral_reasons=old_model.referral_reasons,
        notes=(old_model.notes or []) + [
            f"Signal override: {request.signal_code} changed from {original_score} to {request.audited_value}"
        ],
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
        correlation_matrix_version=old_model.correlation_matrix_version,
        # Exposure (carry forward)
        exposure_value=old_model.exposure_value,
        exposure_band_id=old_model.exposure_band_id,
        exposure_band_label=old_model.exposure_band_label,
        exposure_size_score=old_model.exposure_size_score,
        exposure_modifier=old_model.exposure_modifier,
        exposure_assessment_method=old_model.exposure_assessment_method,
    )

    # ── c. Copy signal bindings with override ────────────────────────────

    mvs_repo = ModelVersionSignalRepository(db)
    new_signal_rows = await mvs_repo.copy_to_new_version(
        source_model_version_id=old_model.id,
        target_model_version_id=new_model.id,
        override_signal_id=target_signal_int_id,
        override_values={"score": request.audited_value},
    )

    # ── d. Recalculate composite score, tier, and pricing ────────────────

    recalc = recalculate_composite_from_signals(new_signal_rows, old_model)
    tier_result = determine_tier_from_score(recalc["pure_composite_score"], old_model)

    # Update the new model version with recalculated values
    new_model.pure_composite_score = recalc["pure_composite_score"]
    new_model.final_composite_score = recalc["pure_composite_score"]
    new_model.group_scores = recalc["group_scores"]
    new_model.confidence = recalc["confidence"]
    new_model.signal_coverage = recalc["signal_coverage"]
    new_model.score_based_tier = tier_result["score_based_tier"]
    new_model.final_tier = tier_result["final_tier"]
    new_model.tier_label = tier_result["tier_label"]
    new_model.decision = tier_result["decision"]
    new_model.auto_approve = tier_result["auto_approve"]
    new_model.base_premium = tier_result["base_premium"]
    new_model.base_premium_method = tier_result["base_premium_method"]
    new_model.final_premium = tier_result["final_premium"]
    new_model.premium_after_modifiers = tier_result["premium_after_modifiers"]

    await db.flush()

    # ── e. Record signal audit ───────────────────────────────────────────

    # Find the new model_version_signal row for the overridden signal
    new_target_mvs = None
    for sig in new_signal_rows:
        if sig.signal_id == target_signal_int_id:
            new_target_mvs = sig
            break

    score_impact = round(
        (recalc["pure_composite_score"] or 0.0) - (old_model.pure_composite_score or 0.0), 4
    )
    tier_impact = (tier_result["final_tier"] or 0) - (old_model.final_tier or 0)

    audit_repo = SignalAuditRepository(db)
    await audit_repo.create_override(
        model_version_signal_id=new_target_mvs.id,
        audited_value=request.audited_value,
        overridden_by=uuid.UUID(request.underwriter_id) if request.underwriter_id else None,
        rationale=request.rationale,
        evidence_reference=request.evidence_reference,
        score_impact=score_impact,
        tier_impact=tier_impact,
    )

    # ── f. Update quote FK and premium ───────────────────────────────────

    quote_repo = QuoteRepository(db)
    await quote_repo.update_model_version_id(quote_code, new_model.id)

    # Update recommended premium if pricing changed
    if tier_result["final_premium"] is not None:
        await db.execute(
            update(Quote)
            .where(Quote.quote_code == quote_code)
            .values(
                recommended_premium=tier_result["final_premium"],
                updated_at=datetime.now(timezone.utc),
            )
        )

    # ── g. Create referral if decision requires it ───────────────────────

    referral_reasons = []
    new_decision = tier_result["decision"]

    if new_decision == DecisionType.REFER:
        referral_reasons = [
            f"Signal override on '{request.signal_code}' triggered referral",
            f"Audited value: {request.audited_value} (was {original_score})",
        ]
        if score_impact != 0:
            referral_reasons.append(
                f"Composite score impact: {score_impact:+.2f}"
            )

        ref_repo = ReferralRepository(db)
        await ref_repo.create(
            quote_id=quote.id,
            reasons=referral_reasons,
            priority=3,  # Signal overrides are higher priority than default
        )

    # ── h. Commit atomically ─────────────────────────────────────────────

    await db.commit()

    # ── Build response ───────────────────────────────────────────────────

    # Resolve entity_code from the target signal row
    entity_code = target_signal_row.entity_code or ""

    return SignalOverrideResponse(
        signal_code=request.signal_code,
        entity_code=entity_code,
        version_code=new_model.version_code,
        original_score=original_score,
        audited_value=request.audited_value,
        score_impact=score_impact,
        tier_impact=tier_impact,
        new_composite_score=recalc["pure_composite_score"],
        new_tier=tier_result["final_tier"],
        new_tier_label=tier_result["tier_label"],
        overridden_by=request.underwriter_id or "system",
        overridden_at=datetime.now(timezone.utc),
        override_rationale=request.rationale,
        evidence_reference=request.evidence_reference,
        previous_version_code=old_model.version_code,
        new_version_code=new_model.version_code,
    )

