"""
DSI Commercial Terms Endpoints

Endpoints for managing commercial terms, offered premium, and risk terms.
These operate on the gross/reporting side of the pricing pipeline:

    model_versions (technical premium) → commercial_terms (gross premium)
                                       → risk_terms (deductible nuance)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    CommercialTermsRecord,
    RiskTermsRecord,
    ModelVersionRecord,
    Quote,
)

from ..types import (
    CommercialTermsDBRecord,
    OfferedPremiumRequest,
    OfferedPremiumResponse,
    EarnedPeriodRequest,
    RiskTermsDBRecord,
)

logger = logging.getLogger("dsi.api.commercial")
router = APIRouter()


# =============================================================================
# COMMERCIAL TERMS — CRUD
# =============================================================================

@router.get(
    "/commercial/{model_version_code}",
    response_model=CommercialTermsDBRecord,
)
async def get_commercial_terms(
    model_version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> CommercialTermsDBRecord:
    """Get commercial terms for a model version."""
    # Resolve model_version_id from code
    mv_query = select(ModelVersionRecord.id).where(
        ModelVersionRecord.version_code == model_version_code
    )
    mv_result = await db.execute(mv_query)
    mv_id = mv_result.scalar_one_or_none()
    if not mv_id:
        raise HTTPException(status_code=404, detail="Model version not found")

    query = select(CommercialTermsRecord).where(
        CommercialTermsRecord.model_version_id == mv_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found for this model version"
        )

    return record


@router.get(
    "/commercial/entity/{entity_id}",
    response_model=List[CommercialTermsDBRecord],
)
async def get_commercial_terms_by_entity(
    entity_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
) -> List[CommercialTermsDBRecord]:
    """Get all commercial terms for an entity, ordered by most recent."""
    query = (
        select(CommercialTermsRecord)
        .where(CommercialTermsRecord.entity_id == entity_id)
        .order_by(CommercialTermsRecord.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.scalars().all()
    return records


# =============================================================================
# OFFERED PREMIUM — underwriter discretion
# =============================================================================

@router.post(
    "/commercial/{model_version_code}/offered-premium",
    response_model=OfferedPremiumResponse,
)
async def set_offered_premium(
    model_version_code: str,
    request: OfferedPremiumRequest,
    db: AsyncSession = Depends(get_async_db),
) -> OfferedPremiumResponse:
    """Set or update the offered premium on commercial terms.

    The offered premium represents the underwriter's final price after
    applying discretion to the calculated gross premium. The discretion
    percentage is computed automatically from the gross premium.
    """
    # Resolve model_version_id from code
    mv_query = select(ModelVersionRecord.id).where(
        ModelVersionRecord.version_code == model_version_code
    )
    mv_result = await db.execute(mv_query)
    mv_id = mv_result.scalar_one_or_none()
    if not mv_id:
        raise HTTPException(status_code=404, detail="Model version not found")

    query = select(CommercialTermsRecord).where(
        CommercialTermsRecord.model_version_id == mv_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found for this model version"
        )

    if not record.gross_premium or record.gross_premium <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot set offered premium: gross premium is not calculated"
        )

    # Validate discretion bounds
    max_discretion = record.offered_premium_discretion or 0.10
    gross = record.gross_premium
    discretion_applied = (request.offered_premium - gross) / gross

    if abs(discretion_applied) > max_discretion:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Offered premium {request.offered_premium:,.2f} exceeds "
                f"discretion bounds of ±{max_discretion:.0%} on gross "
                f"premium {gross:,.2f}. Allowed range: "
                f"{gross * (1 - max_discretion):,.2f} to "
                f"{gross * (1 + max_discretion):,.2f}"
            ),
        )

    now = datetime.now(timezone.utc)
    record.offered_premium = request.offered_premium
    record.offered_premium_rationale = request.offered_premium_rationale
    record.offered_premium_set_at = now
    record.updated_at = now

    await db.commit()
    await db.refresh(record)

    return OfferedPremiumResponse(
        commercial_terms_id=str(record.id),
        offered_premium=record.offered_premium,
        offered_premium_discretion=discretion_applied,
        gross_premium=record.gross_premium,
        offered_premium_rationale=record.offered_premium_rationale,
        offered_premium_set_at=record.offered_premium_set_at,
    )


# =============================================================================
# EARNED PERIOD — written/earned time values
# =============================================================================

@router.post(
    "/commercial/{model_version_code}/earned-period",
)
async def set_earned_period(
    model_version_code: str,
    request: EarnedPeriodRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Set the written date and earned period on commercial terms."""
    mv_query = select(ModelVersionRecord.id).where(
        ModelVersionRecord.version_code == model_version_code
    )
    mv_result = await db.execute(mv_query)
    mv_id = mv_result.scalar_one_or_none()
    if not mv_id:
        raise HTTPException(status_code=404, detail="Model version not found")

    query = select(CommercialTermsRecord).where(
        CommercialTermsRecord.model_version_id == mv_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found for this model version"
        )

    if request.earned_end <= request.earned_start:
        raise HTTPException(
            status_code=400,
            detail="earned_end must be after earned_start"
        )

    record.written_date = request.written_date or datetime.now(timezone.utc)
    record.earned_start = request.earned_start
    record.earned_end = request.earned_end
    record.earned_method = request.earned_method
    record.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "status": "ok",
        "written_date": str(record.written_date),
        "earned_start": str(record.earned_start),
        "earned_end": str(record.earned_end),
        "earned_method": record.earned_method,
    }


# =============================================================================
# RISK TERMS — deductible nuance for reporting
# =============================================================================

@router.get(
    "/commercial/{model_version_code}/risk-terms",
    response_model=RiskTermsDBRecord,
)
async def get_risk_terms(
    model_version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> RiskTermsDBRecord:
    """Get risk terms (deductible nuance) for a model version."""
    mv_query = select(ModelVersionRecord.id).where(
        ModelVersionRecord.version_code == model_version_code
    )
    mv_result = await db.execute(mv_query)
    mv_id = mv_result.scalar_one_or_none()
    if not mv_id:
        raise HTTPException(status_code=404, detail="Model version not found")

    ct_query = select(CommercialTermsRecord.id).where(
        CommercialTermsRecord.model_version_id == mv_id
    )
    ct_result = await db.execute(ct_query)
    ct_id = ct_result.scalar_one_or_none()
    if not ct_id:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found for this model version"
        )

    query = select(RiskTermsRecord).where(
        RiskTermsRecord.commercial_terms_id == ct_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Risk terms not found for this model version"
        )

    return record


@router.post(
    "/commercial/{model_version_code}/risk-terms",
    response_model=RiskTermsDBRecord,
)
async def set_risk_terms(
    model_version_code: str,
    request: RiskTermsDBRecord,
    db: AsyncSession = Depends(get_async_db),
) -> RiskTermsDBRecord:
    """Set or update risk terms for a model version."""
    mv_query = select(ModelVersionRecord.id).where(
        ModelVersionRecord.version_code == model_version_code
    )
    mv_result = await db.execute(mv_query)
    mv_id = mv_result.scalar_one_or_none()
    if not mv_id:
        raise HTTPException(status_code=404, detail="Model version not found")

    ct_query = select(CommercialTermsRecord).where(
        CommercialTermsRecord.model_version_id == mv_id
    )
    ct_result = await db.execute(ct_query)
    ct_record = ct_result.scalar_one_or_none()
    if not ct_record:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found — create commercial terms first"
        )

    # Check for existing risk terms
    existing_query = select(RiskTermsRecord).where(
        RiskTermsRecord.commercial_terms_id == ct_record.id
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing
        for field_name, value in request.model_dump(exclude_unset=True).items():
            if field_name not in ("created_at", "updated_at"):
                setattr(existing, field_name, value)
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Create new
        record = RiskTermsRecord(
            id=uuid.uuid4(),
            commercial_terms_id=ct_record.id,
            **request.model_dump(exclude={"created_at", "updated_at"}),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
