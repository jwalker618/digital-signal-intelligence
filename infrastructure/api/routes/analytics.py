"""
DSI Analytics Endpoints (Phase 11)

Endpoints for portfolio and workflow analytics.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

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
):
    """
    Get portfolio-level analytics.

    Provides summary metrics for submissions, quotes, and binds.
    """
    now = datetime.utcnow()

    # Calculate period dates
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

    # Mock portfolio data
    return PortfolioSummaryResponse(
        as_of_date=now,
        coverage=coverage,
        period=f"{start} to {now.date()}",
        total_submissions=150,
        total_quotes=135,
        total_binds=45,
        total_declines=15,
        gross_written_premium=2250000,
        quoted_premium=3500000,
        average_premium=50000,
        average_score=725,
        average_tier=2.3,
        tier_distribution={1: 25, 2: 55, 3: 40, 4: 20, 5: 10},
        quote_rate=0.90,
        bind_rate=0.33,
        decline_rate=0.10,
    )


@router.get("/analytics/turnaround", response_model=TurnaroundMetricsResponse)
async def get_turnaround_metrics(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    period: str = Query("last30", description="Period for analysis"),
):
    """
    Get workflow turnaround metrics.

    Measures time-to-quote, time-to-decision, and SLA compliance.
    """
    return TurnaroundMetricsResponse(
        period=period,
        sample_size=150,
        avg_time_to_quote=4.2,
        avg_time_to_decision=6.8,
        p50_time_to_quote=3.5,
        p90_time_to_quote=8.2,
        p95_time_to_quote=12.5,
        sla_target_hours=24.0,
        sla_compliance_rate=0.92,
        time_by_tier={1: 2.5, 2: 3.8, 3: 5.2, 4: 8.5, 5: 15.0},
    )


@router.get("/analytics/signals", response_model=SignalHealthResponse)
async def get_signal_health(
    coverage: str = Query(..., description="Coverage type"),
    period: str = Query("last30", description="Period for analysis"),
):
    """
    Get signal extraction health metrics.

    Monitors signal coverage, extraction rates, and quality issues.
    """
    return SignalHealthResponse(
        coverage=coverage,
        period=period,
        overall_coverage=0.94,
        group_coverage={
            "financial": 0.96,
            "security": 0.92,
            "governance": 0.95,
            "operational": 0.88,
        },
        signal_coverage={
            "revenue_growth": 0.98,
            "profitability": 0.95,
            "email_security": 0.91,
            "web_security": 0.89,
            "leadership_stability": 0.97,
        },
        issues=[
            {
                "signal_id": "dnb_score",
                "issue_type": "low_coverage",
                "severity": "warning",
                "description": "Signal extraction coverage is 72%",
            },
        ],
    )


# =============================================================================
# TIER DISTRIBUTION
# =============================================================================

@router.get("/analytics/tiers")
async def get_tier_distribution(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    period: str = Query("last30", description="Period for analysis"),
):
    """
    Get detailed tier distribution analytics.
    """
    return {
        "period": period,
        "coverage": coverage or "all",
        "distribution": {
            "1": {"count": 25, "percentage": 0.17, "premium": 375000},
            "2": {"count": 55, "percentage": 0.37, "premium": 825000},
            "3": {"count": 40, "percentage": 0.27, "premium": 600000},
            "4": {"count": 20, "percentage": 0.13, "premium": 300000},
            "5": {"count": 10, "percentage": 0.07, "premium": 150000},
        },
        "trend": {
            "tier_1_change": 0.02,  # +2% vs prior period
            "tier_5_change": -0.01,  # -1% vs prior period
            "avg_tier_change": -0.05,  # Improving (lower avg tier)
        },
    }


# =============================================================================
# FUNNEL ANALYTICS
# =============================================================================

@router.get("/analytics/funnel")
async def get_submission_funnel(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    period: str = Query("last30", description="Period for analysis"),
):
    """
    Get submission to bind conversion funnel.
    """
    return {
        "period": period,
        "coverage": coverage or "all",
        "stages": {
            "submissions": 150,
            "processed": 148,
            "quoted": 135,
            "referred": 20,
            "declined": 15,
            "bound": 45,
            "not_taken_up": 75,
        },
        "rates": {
            "processing_rate": 0.99,
            "quote_rate": 0.91,
            "referral_rate": 0.13,
            "decline_rate": 0.10,
            "bind_rate": 0.33,
            "ntu_rate": 0.56,
        },
        "avg_times": {
            "time_to_quote_hours": 4.2,
            "time_to_bind_hours": 72.5,
            "time_to_decline_hours": 8.0,
        },
    }


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@router.get("/analytics/performance")
async def get_performance_metrics(
    coverage: str = Query(..., description="Coverage type"),
    period: str = Query("last90", description="Period for analysis"),
):
    """
    Get model performance metrics.

    Shows how well DSI predictions correlate with outcomes.
    """
    return {
        "coverage": coverage,
        "period": period,
        "sample_size": 250,
        "metrics": {
            "tier_accuracy": 0.78,  # % correct tier predictions
            "score_correlation": 0.65,  # Correlation with loss outcomes
            "gini_coefficient": 0.42,
            "systematic_bias": -0.02,  # Slight over-optimism
        },
        "tier_performance": {
            "1": {"expected_loss_ratio": 0.35, "actual_loss_ratio": 0.32, "sample": 40},
            "2": {"expected_loss_ratio": 0.45, "actual_loss_ratio": 0.48, "sample": 80},
            "3": {"expected_loss_ratio": 0.55, "actual_loss_ratio": 0.52, "sample": 70},
            "4": {"expected_loss_ratio": 0.70, "actual_loss_ratio": 0.68, "sample": 40},
            "5": {"expected_loss_ratio": 0.90, "actual_loss_ratio": 0.95, "sample": 20},
        },
    }


# =============================================================================
# UNDERWRITER METRICS
# =============================================================================

@router.get("/analytics/underwriters")
async def get_underwriter_metrics(
    underwriter_id: Optional[str] = Query(None, description="Specific underwriter"),
    period: str = Query("last30", description="Period for analysis"),
):
    """
    Get underwriter activity and performance metrics.
    """
    underwriters = [
        {
            "underwriter_id": "UW_001",
            "name": "John Smith",
            "submissions_reviewed": 45,
            "referrals_handled": 12,
            "approval_rate": 0.83,
            "avg_response_hours": 3.2,
            "premium_written": 850000,
        },
        {
            "underwriter_id": "UW_002",
            "name": "Jane Doe",
            "submissions_reviewed": 52,
            "referrals_handled": 15,
            "approval_rate": 0.80,
            "avg_response_hours": 4.1,
            "premium_written": 920000,
        },
        {
            "underwriter_id": "UW_003",
            "name": "Bob Johnson",
            "submissions_reviewed": 38,
            "referrals_handled": 8,
            "approval_rate": 0.88,
            "avg_response_hours": 2.8,
            "premium_written": 650000,
        },
    ]

    if underwriter_id:
        underwriters = [u for u in underwriters if u["underwriter_id"] == underwriter_id]

    return {
        "period": period,
        "underwriters": underwriters,
        "team_totals": {
            "total_reviewed": sum(u["submissions_reviewed"] for u in underwriters),
            "total_referrals": sum(u["referrals_handled"] for u in underwriters),
            "avg_approval_rate": sum(u["approval_rate"] for u in underwriters) / len(underwriters),
            "total_premium": sum(u["premium_written"] for u in underwriters),
        },
    }


# =============================================================================
# DASHBOARD DATA
# =============================================================================

@router.get("/analytics/dashboard")
async def get_dashboard_data(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
):
    """
    Get complete dashboard data in a single call.
    """
    now = datetime.utcnow()

    return {
        "as_of": now,
        "coverage": coverage or "all",
        "kpis": [
            {
                "title": "Gross Written Premium",
                "value": 2250000,
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
                "trend_direction": "up",  # Lower is better
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
        "premium_trend": {
            "labels": ["Oct", "Nov", "Dec"],
            "datasets": [
                {"label": "GWP", "data": [650000, 750000, 850000]},
            ],
        },
        "pending_referrals": 5,
        "sla_compliance": 0.92,
    }
