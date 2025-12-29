"""
DSI Quote Endpoints (Phase 11)

Endpoints for retrieving and managing quotes.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..types import (
    QuoteResponse,
    QuoteListItem,
    QuoteStatus,
    DiscoverySummary,
    SignalSummary,
)


logger = logging.getLogger("dsi.api.quotes")

router = APIRouter()


# =============================================================================
# IN-MEMORY STORAGE (Replace with database)
# =============================================================================

_quotes: dict = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def create_mock_quote(quote_id: str, submission_id: str, entity_name: str, coverage: str) -> dict:
    """Create a mock quote for demonstration."""
    now = datetime.utcnow()

    return {
        "quote_id": quote_id,
        "submission_id": submission_id,
        "entity_name": entity_name,
        "coverage": coverage,
        "status": QuoteStatus.READY,
        "composite_score": 742,
        "tier": 2,
        "tier_label": "STANDARD",
        "decision": "approve",
        "premium_options": {
            "1000000": 12500,
            "2000000": 18750,
            "5000000": 31250,
        },
        "recommended_premium": 18750,
        "recommended_limit": 2000000,
        "discovery": {
            "domain": "example.com",
            "confidence": "high",
            "industry": "Technology",
            "employee_count": 500,
        },
        "signal_summary": {
            "total_signals": 25,
            "signals_extracted": 23,
            "top_factors": [
                {"signal": "financial_health", "impact": "positive", "score": 85},
                {"signal": "security_posture", "impact": "positive", "score": 78},
                {"signal": "regulatory_compliance", "impact": "neutral", "score": 65},
            ],
        },
        "referral_reasons": [],
        "referral_id": None,
        "valid_until": now + timedelta(days=30),
        "created_at": now,
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/quotes", response_model=List[QuoteListItem])
async def list_quotes(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List quotes with optional filtering.
    """
    results = list(_quotes.values())

    # Apply filters
    if coverage:
        results = [q for q in results if q["coverage"] == coverage]

    if status:
        results = [q for q in results if q["status"].value == status]

    # Sort by created_at descending
    results.sort(key=lambda q: q["created_at"], reverse=True)

    # Paginate
    results = results[offset:offset + limit]

    return [
        QuoteListItem(
            quote_id=q["quote_id"],
            submission_id=q["submission_id"],
            entity_name=q["entity_name"],
            coverage=q["coverage"],
            status=q["status"],
            tier=q["tier"],
            premium=q["recommended_premium"] or 0,
            created_at=q["created_at"],
        )
        for q in results
    ]


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str):
    """
    Get quote details by ID.
    """
    if quote_id not in _quotes:
        # Create mock quote for demonstration
        _quotes[quote_id] = create_mock_quote(
            quote_id=quote_id,
            submission_id=generate_id("sub"),
            entity_name="Demo Company",
            coverage="cyber",
        )

    q = _quotes[quote_id]

    discovery = None
    if q.get("discovery"):
        discovery = DiscoverySummary(
            domain=q["discovery"]["domain"],
            confidence=q["discovery"]["confidence"],
            industry=q["discovery"].get("industry"),
            employee_count=q["discovery"].get("employee_count"),
        )

    signal_summary = None
    if q.get("signal_summary"):
        signal_summary = SignalSummary(
            total_signals=q["signal_summary"]["total_signals"],
            signals_extracted=q["signal_summary"]["signals_extracted"],
            top_factors=q["signal_summary"]["top_factors"],
        )

    return QuoteResponse(
        quote_id=q["quote_id"],
        submission_id=q["submission_id"],
        status=q["status"],
        composite_score=q["composite_score"],
        tier=q["tier"],
        tier_label=q["tier_label"],
        decision=q["decision"],
        premium_options=q["premium_options"],
        recommended_premium=q["recommended_premium"],
        recommended_limit=q["recommended_limit"],
        discovery=discovery,
        signal_summary=signal_summary,
        referral_reasons=q["referral_reasons"],
        referral_id=q.get("referral_id"),
        valid_until=q["valid_until"],
        created_at=q["created_at"],
    )


@router.post("/quotes/{quote_id}/bind")
async def bind_quote(quote_id: str):
    """
    Bind a quote (convert to policy).
    """
    if quote_id not in _quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    q = _quotes[quote_id]

    if q["status"] != QuoteStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot bind quote in status {q['status'].value}"
        )

    # Check if expired
    if q["valid_until"] < datetime.utcnow():
        q["status"] = QuoteStatus.EXPIRED
        raise HTTPException(status_code=400, detail="Quote has expired")

    # Bind
    q["status"] = QuoteStatus.BOUND
    q["bound_at"] = datetime.utcnow()

    return {
        "message": "Quote bound successfully",
        "quote_id": quote_id,
        "policy_id": generate_id("pol"),
        "bound_at": q["bound_at"],
    }


@router.post("/quotes/{quote_id}/decline")
async def decline_quote(quote_id: str, reason: Optional[str] = None):
    """
    Decline a quote.
    """
    if quote_id not in _quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    q = _quotes[quote_id]

    if q["status"] not in [QuoteStatus.READY, QuoteStatus.REFERRED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot decline quote in status {q['status'].value}"
        )

    q["status"] = QuoteStatus.DECLINED
    q["declined_at"] = datetime.utcnow()
    q["decline_reason"] = reason

    return {
        "message": "Quote declined",
        "quote_id": quote_id,
        "declined_at": q["declined_at"],
    }


@router.get("/quotes/{quote_id}/signals")
async def get_quote_signals(quote_id: str):
    """
    Get detailed signal breakdown for a quote.
    """
    if quote_id not in _quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Return mock signal details
    return {
        "quote_id": quote_id,
        "signal_groups": {
            "financial": {
                "weight": 0.25,
                "signals": [
                    {"id": "revenue_growth", "score": 78, "contribution": 0.05},
                    {"id": "profitability", "score": 82, "contribution": 0.06},
                    {"id": "liquidity", "score": 71, "contribution": 0.04},
                ],
            },
            "security": {
                "weight": 0.30,
                "signals": [
                    {"id": "email_security", "score": 85, "contribution": 0.08},
                    {"id": "web_security", "score": 72, "contribution": 0.06},
                    {"id": "vulnerability_mgmt", "score": 68, "contribution": 0.05},
                ],
            },
            "governance": {
                "weight": 0.20,
                "signals": [
                    {"id": "leadership_stability", "score": 90, "contribution": 0.06},
                    {"id": "regulatory_compliance", "score": 65, "contribution": 0.04},
                ],
            },
        },
    }


@router.get("/quotes/{quote_id}/premium-options")
async def get_premium_options(
    quote_id: str,
    limits: Optional[List[int]] = Query(None, description="Specific limits to price"),
):
    """
    Get premium options for various limits.
    """
    if quote_id not in _quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    q = _quotes[quote_id]

    # Use stored options or calculate new ones
    if limits:
        # Calculate for requested limits
        base_rate = 0.00625  # Simplified rate
        tier_factor = {1: 0.8, 2: 1.0, 3: 1.2, 4: 1.5, 5: 2.0}.get(q["tier"], 1.0)

        options = {}
        for limit in limits:
            premium = limit * base_rate * tier_factor
            options[str(limit)] = round(premium, 2)

        return {"quote_id": quote_id, "premium_options": options}

    return {
        "quote_id": quote_id,
        "premium_options": q["premium_options"],
        "recommended_limit": q["recommended_limit"],
        "recommended_premium": q["recommended_premium"],
    }
