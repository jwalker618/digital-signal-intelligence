"""
DSI Model Version Endpoints (Phase 11) - Database Backed

Endpoints for retrieving risk terms.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db

from infrastructure.db.models import (
    RiskTermsRecord,
    ModelVersionRecord,
)

from ..types import (
    RiskTermsDBRecord,
)

logger = logging.getLogger("dsi.api.riskterms")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/riskterms/{version_code}",response_model=RiskTermsDBRecord)
async def get_risk_terms(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> RiskTermsDBRecord:

    query = (
        select(RiskTermsRecord)
        .join(ModelVersionRecord, RiskTermsRecord.model_version_id ==  ModelVersionRecord.id)
        .where(ModelVersionRecord.version_code == version_code)
    )

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Risk terms not found for this model version"
        )

    return record

