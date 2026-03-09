"""
DSI Frontend Endpoints (CQRS Read Models)

Endpoints for retrieving and managing frontend data.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db
from ..types import FrontendSubmissionPipeline

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
                    q.status,
                    q.recommended_premium,
                    q.recommended_limit,
                    mv.pure_composite_score,
                    mv.final_tier,
                    mv.tier_label,
                    mv.decision
             
                FROM submissions s
                    LEFT JOIN quotes q ON s.id = q.submission_id
                    LEFT JOIN referrals r on r.quote_id = q.id
                    LEFT JOIN model_versions mv ON mv.submission_id = s.id AND mv.id = q.model_version_id
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
