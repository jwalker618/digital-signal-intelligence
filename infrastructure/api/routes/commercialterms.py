"""
DSI Model Version Endpoints (Phase 11) - Database Backed

Endpoints for retrieving commercial terms.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db

from infrastructure.db.models import (
    CommercialTermsRecord,
    ModelVersionRecord,
)

from ..types import (
    CommercialTermsDBRecord,
)

logger = logging.getLogger("dsi.api.commercialterms")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/commercialterms/{version_code}",response_model=CommercialTermsDBRecord)
async def get_commercial_terms(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> CommercialTermsDBRecord:
    
    query = (
        select(CommercialTermsRecord)
        .join(ModelVersionRecord, CommercialTermsRecord.model_version_id == ModelVersionRecord.id)
        .where(ModelVersionRecord.version_code == version_code)
    )
    
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Commercial terms not found for this model version"
        )

    return record
