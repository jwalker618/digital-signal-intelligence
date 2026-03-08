"""
DSI Model Version Endpoints (Phase 11) - Database Backed

Endpoints for retrieving model versions.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from ..types import (
    ModelVersionDBRecord_BaseOnly, 
    ModelVersionDBRecord_DetailOnly, 
    ModelVersionDBRecord_CommentaryOnly, 
    ModelVersionDBRecord_ExposureOnly,
    ModelVersionDBRecord_LossOnly
)

logger = logging.getLogger("dsi.api.modelversions")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/modelversion/{version_code}", response_model=ModelVersionDBRecord_BaseOnly)
async def get_modelversion_base(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_BaseOnly:
    """Get model version details by code."""
    query = select(ModelVersionDBRecord_BaseOnly).where(ModelVersionDBRecord_BaseOnly.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ModelVersionDBRecord_BaseOnly(
        version_code=row.version_code,
        version_number=row.version_number,
        version_type=row.version_type,
        is_latest=row.is_latest,
        coverage=row.coverage,
        configuration_name=row.configuration_name,
        pure_composite_score=row.pure_composite_score,
        confidence=row.confidence,
        signal_coverage=row.signal_coverage,
        signal_conditions=row.signal_conditions,
        query_conditions=row.query_conditions,
        tier_overrides=row.tier_overrides,
        score_based_tier=row.score_based_tier,
        final_tier=row.final_tier,
        tier_label=row.tier_label,
        base_premium=row.base_premium,
        base_premium_method=row.base_premium_method,
        modifiers_applied=row.modifiers_applied,
        premium_after_modifiers=row.premium_after_modifiers,
        limit_premiums=row.limit_premiums,
        final_premium=row.final_premium,
        decision=row.decision,
        auto_approve=row.auto_approve,
    )

@router.get("/modelversion/{version_code}", response_model=ModelVersionDBRecord_DetailOnly)
async def get_modelversion_detail(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_DetailOnly:
    """Get model version details by code."""
    query = select(ModelVersionDBRecord_DetailOnly).where(ModelVersionDBRecord_DetailOnly.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ModelVersionDBRecord_DetailOnly(
        version_code=row.version_code,
        discovery_output=row.discovery_output,
        signal_outputs=row.signal_outputs,
        categorical_outputs=row.categorical_outputs,
        group_scores=row.group_scores
    )

@router.get("/modelversion/{version_code}", response_model=ModelVersionDBRecord_CommentaryOnly)
async def get_modelversion_commentary(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_CommentaryOnly:
    """Get model version details by code."""
    query = select(ModelVersionDBRecord_CommentaryOnly).where(ModelVersionDBRecord_CommentaryOnly.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ModelVersionDBRecord_CommentaryOnly(
        version_code=row.version_code,
        referral_reasons=row.referral_reasons,
        notes=row.notes
    )

@router.get("/modelversion/{version_code}", response_model=ModelVersionDBRecord_LossOnly)
async def get_modelversion_loss(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_LossOnly:
    """Get model version details by code."""
    query = select(ModelVersionDBRecord_LossOnly).where(ModelVersionDBRecord_LossOnly.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ModelVersionDBRecord_LossOnly(
        version_code=row.version_code,
        loss_propensity_score=row.loss_propensity_score,
        severity_propensity_score=row.severity_propensity_score,
        loss_propensity_band=row.loss_propensity_band,
        severity_propensity_band=row.severity_propensity_band,
        loss_confidence=row.loss_confidence,
        loss_cohort_code=row.loss_cohort_code,
        loss_cohort_name=row.loss_cohort_name,
        loss_cohort_confidence=row.loss_cohort_confidence,
        loss_frequency_multiplier=row.loss_frequency_multiplier,
        loss_severity_multiplier=row.loss_severity_multiplier,
        loss_combined_modifier=row.loss_combined_modifier,
        loss_trend_direction=row.loss_trend_direction,
        loss_previous_score=row.loss_previous_score,
        loss_score_velocity=row.loss_score_velocity,
        loss_last_refresh=row.loss_last_refresh,
        correlation_matrix_version=row.correlation_matrix_version
    )

@router.get("/modelversion/{version_code}", response_model=ModelVersionDBRecord_ExposureOnly)
async def get_modelversion_exposure(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_ExposureOnly:
    """Get model version details by code."""
    query = select(ModelVersionDBRecord_ExposureOnly).where(ModelVersionDBRecord_ExposureOnly.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    return ModelVersionDBRecord_ExposureOnly(
        version_code=row.version_code,
        exposure_value=row.exposure_value,
        exposure_band_id=row.exposure_band_id,
        exposure_band_label=row.exposure_band_label,
        exposure_magnitude_score=row.exposure_magnitude_score,
        exposure_modifier=row.exposure_modifier,
        exposure_assessment_method=row.exposure_assessment_method
    )