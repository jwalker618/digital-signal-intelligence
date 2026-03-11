"""
DSI Analytics Endpoints (Phase 11)

Endpoints for portfolio and workflow analytics.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    ModelVersionRecord, 
    Submission,
)

from ..types import (
    PortfolioSummaryResponse,
    TurnaroundMetricsResponse,
    SignalHealthResponse,
)

logger = logging.getLogger("dsi.api.analytics")

router = APIRouter()

# =============================================================================
# PORTFOLIO ANALYTICS
# =============================================================================

@router.get("/analytics/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    period: str = Query("mtd", description="Period: mtd, qtd, ytd, last30, last90"),
) -> PortfolioSummaryResponse:
    """
    Get portfolio-level analytics.
    Provides summary metrics for submissions, quotes, and binds.
    """
    now = datetime.utcnow()

    if period == "mtd":
        start = date(now.year, now.month, 1)
    elif period == "qtd":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start = date(now.year, quarter_start_month, 1)
    elif period == "ytd":
        start = date(now.year, 1, 1)
    elif period == "last30":
        start = (now - timedelta(days=30)).date()
    elif period == "last90":
        start = (now - timedelta(days=90)).date()
    else:
        start = date(now.year, now.month, 1)

    return PortfolioSummaryResponse(
        as_of_date=now,
        coverage=coverage or "all",
        period=period,
        total_submissions=150,
        total_quotes=135,
        total_binds=45,
        total_declines=15,
        gross_written_premium=2_250_000.0,
        quoted_premium=6_750_000.0,
        average_premium=50_000.0,
        average_score=78.5,
        average_tier=2.4,
        tier_distribution={
            1: 25,
            2: 55,
            3: 40,
            4: 20,
            5: 10,
        },
        quote_rate=0.90,
        bind_rate=0.33,
        decline_rate=0.10,
    )


@router.get("/analytics/dashboard")
async def get_dashboard_data(
    coverage: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Get aggregated data for dashboard visualizations."""
    return {
        "coverage_filter": coverage or "all",
        "kpis": [
            {
                "title": "Gross Written Premium",
                "value": 2_250_000,
                "format": "currency",
                "trend": 0.12,
                "trend_direction": "up",
            },
            {
                "title": "Total Submissions",
                "value": 150,
                "format": "number",
                "trend": 0.08,
                "trend_direction": "up",
            },
            {
                "title": "Bind Rate",
                "value": 0.33,
                "format": "percentage",
                "trend": 0.02,
                "trend_direction": "up",
            },
            {
                "title": "Avg Quote Time",
                "value": 4.2,
                "format": "hours",
                "trend": -0.5,
                "trend_direction": "up",
            },
        ],
        "tier_distribution": {
            "labels": ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"],
            "data": [25, 55, 40, 20, 10],
        },
        "funnel": {
            "labels": ["Submissions", "Quoted", "Bound"],
            "data": [150, 135, 45],
        },
    }

# =============================================================================
# SUBMISSION ANALYTICS
# =============================================================================

@router.get("/analytics/loss/scatter-plot")
async def get_loss_scatter_data(
    coverage: str,
    created_after: datetime,
    limit: int = 500,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component B: Lightweight coordinate payload for the scatter plot."""
    
    query = (
        select(
            ModelVersionRecord.version_id,
            ModelVersionRecord.loss_propensity_score.label("x_propensity"),
            ModelVersionRecord.severity_propensity_score.label("y_severity"),
            ModelVersionRecord.decision
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after
        )
        .limit(limit)
    )

    result = await db.execute(query)
    return [dict(row) for row in result.mappings().all()]

@router.get("/analytics/loss/cohort-benchmarks")
async def get_cohort_benchmarks(
    coverage: str,
    created_after: datetime,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component C: Averages the loss modifiers grouped by cohort."""
    
    query = (
        select(
            ModelVersionRecord.loss_cohort_name.label("cohort_name"),
            func.count(ModelVersionRecord.id).label("peer_count"),
            func.avg(ModelVersionRecord.loss_combined_modifier).label("avg_modifier"),
            func.avg(ModelVersionRecord.loss_propensity_score).label("avg_propensity")
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after,
            ModelVersionRecord.loss_cohort_name.is_not(None)
        )
        .group_by(ModelVersionRecord.loss_cohort_name)
    )

    result = await db.execute(query)
    rows = result.mappings().all()
    
    # Format the floats safely
    return [
        {
            "cohort_name": row["cohort_name"],
            "peer_count": row["peer_count"],
            "avg_modifier": round(row["avg_modifier"], 3) if row["avg_modifier"] else 1.0,
            "avg_propensity": round(row["avg_propensity"], 1) if row["avg_propensity"] else 0.0,
        }
        for row in rows
    ]

@router.get("/analytics/loss/trend-distribution")
async def get_trend_distribution(
    coverage: str,
    created_after: datetime,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component D: Counts the frequency of each trend direction."""
    
    query = (
        select(
            ModelVersionRecord.loss_trend_direction.label("trend"),
            func.count(ModelVersionRecord.id).label("count")
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after,
            ModelVersionRecord.loss_trend_direction.is_not(None)
        )
        .group_by(ModelVersionRecord.loss_trend_direction)
    )

    result = await db.execute(query)
    return [dict(row) for row in result.mappings().all()]

@router.get("/analytics/exposure/scatter-plot")
async def get_exposure_scatter_data(
    coverage: str,
    created_after: datetime,
    limit: int = 500,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component B: Coordinate payload mapping Exposure Magnitude against Composite Score."""
    
    query = (
        select(
            ModelVersionRecord.version_id,
            ModelVersionRecord.exposure_magnitude_score.label("x_magnitude"),
            ModelVersionRecord.pure_composite_score.label("y_composite"),
            ModelVersionRecord.decision
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after
        )
        .limit(limit)
    )

    result = await db.execute(query)
    return [dict(row) for row in result.mappings().all()]

@router.get("/analytics/exposure/band-benchmarks")
async def get_exposure_band_benchmarks(
    coverage: str,
    created_after: datetime,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component C: Averages the exposure modifiers grouped by band (e.g., Large, SME)."""
    
    query = (
        select(
            ModelVersionRecord.exposure_band_label.label("band_label"),
            func.count(ModelVersionRecord.id).label("peer_count"),
            func.avg(ModelVersionRecord.exposure_modifier).label("avg_modifier"),
            func.avg(ModelVersionRecord.exposure_value).label("avg_exposure_value")
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after,
            ModelVersionRecord.exposure_band_label.is_not(None)
        )
        .group_by(ModelVersionRecord.exposure_band_label)
    )

    result = await db.execute(query)
    rows = result.mappings().all()
    
    return [
        {
            "band_label": row["band_label"],
            "peer_count": row["peer_count"],
            "avg_modifier": round(row["avg_modifier"], 3) if row["avg_modifier"] else 1.0,
            "avg_exposure_value": float(row["avg_exposure_value"]) if row["avg_exposure_value"] else 0.0,
        }
        for row in rows
    ]

@router.get("/analytics/exposure/tier-distribution")
async def get_exposure_tier_distribution(
    coverage: str,
    created_after: datetime,
    db: AsyncSession = Depends(get_async_db),
) -> List[Dict[str, Any]]:
    """Component D: Shows the average exposure magnitude per Final Tier."""
    
    query = (
        select(
            ModelVersionRecord.final_tier.label("tier"),
            func.avg(ModelVersionRecord.exposure_magnitude_score).label("avg_magnitude"),
            func.count(ModelVersionRecord.id).label("peer_count")
        )
        .select_from(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(
            ModelVersionRecord.is_latest == True,
            Submission.coverage == coverage,
            Submission.created_at >= created_after,
            ModelVersionRecord.final_tier.is_not(None)
        )
        .group_by(ModelVersionRecord.final_tier)
        .order_by(ModelVersionRecord.final_tier)
    )

    result = await db.execute(query)
    rows = result.mappings().all()
    return [{"tier": f"Tier {row['tier']}", "avg_magnitude": round(row["avg_magnitude"] or 0, 1), "peer_count": row["peer_count"]} for row in rows]

