"""
DSI Frontend Endpoints (CQRS Read Models)

Endpoints for retrieving and managing frontend data.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db

from infrastructure.db.models import (
    ModelVersionRecord,
    ModelVersionSignal,
    SignalCache,
    Signal,
)

from ..types import (
    FrontendSubmissionPipeline, 
    FrontendRiskAssessment,
)

logger = logging.getLogger("dsi.api.frontend")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/frontend/pipeline", response_model=List[FrontendSubmissionPipeline])
async def get_frontend_pipeline(
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
) -> List[FrontendSubmissionPipeline]:
    """
    Get highly optimized, read-only pipeline data for frontend grids.
    Safely flattens relational data using ORM joins.
    """
    if created_after is None:
        created_after = datetime.utcnow() - timedelta(days=30)

    query = text("""
                SELECT
                    s.submission_code,
                    q.quote_code,
                    r.referral_code,
                    mv.version_code,

                    s.entity_name,
                    COALESCE(s.coverage, '') || ' / ' || COALESCE(s.configuration, '') AS coverage_configuration,
                    s.created_at,
                    CAST(q.status AS TEXT) AS status,
                    CAST(s.status AS TEXT) AS submission_status,
                    q.recommended_premium,
                    q.recommended_limit,
                    mv.final_premium,
                    mv.final_composite_score,
                    mv.final_tier,
                    mv.tier_label,
                    mv.decision,
                    CAST(r.status AS TEXT) AS referral_state,
                    b.name AS broker_name

                FROM submissions s
                    LEFT JOIN quotes q ON s.id = q.submission_id
                    LEFT JOIN referrals r on r.quote_id = q.id
                    LEFT JOIN model_versions mv ON mv.submission_id = s.id AND mv.id = q.model_version_id
                    LEFT JOIN brokers b ON s.broker_id = b.id
                WHERE mv.is_latest = true
                    AND (
                            CAST(s.status AS TEXT) ILIKE 'draft'
                            OR s.created_at >= :created_after
                        )
            """
    )

    try:
        # Execute the query and get the rows as dictionaries
        result = await db.execute(query, {"created_after": created_after})
        rows = result.mappings().all()

        # Unpack the dictionaries directly into your Pydantic model
        return [FrontendSubmissionPipeline(**row) for row in rows]

    except Exception as e:
        logger.error("DB get frontend pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch pipeline data")

@router.get("/frontend/{version_code}/signals", response_model=List[FrontendRiskAssessment])
async def get_frontend_modelsignals(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> List[FrontendRiskAssessment]:

# Select the exact columns mapping to your Pydantic model
    query = (
        select(
            ModelVersionSignal.signal_id,
            ModelVersionSignal.score,
            ModelVersionSignal.weight,
            ModelVersionSignal.group_weight,
            ModelVersionSignal.contribution,
            ModelVersionSignal.group_code,
            ModelVersionSignal.proxy_tier,
            ModelVersionSignal.expectation_level,
            ModelVersionSignal.was_absent,
            Signal.code
        )
        .select_from(ModelVersionSignal)
        .join(ModelVersionRecord, ModelVersionSignal.model_version_id == ModelVersionRecord.id)
        .join(Signal, ModelVersionSignal.signal_id == Signal.id)
        .where(ModelVersionRecord.version_code == version_code)
        .where(ModelVersionRecord.is_latest == True) 
    )
    
    result = await db.execute(query)
    rows = result.mappings().all()

    # Return empty list if none found (better than 404 for UI grids)
    if not rows:
        return []

    return [FrontendRiskAssessment(**row) for row in rows]

