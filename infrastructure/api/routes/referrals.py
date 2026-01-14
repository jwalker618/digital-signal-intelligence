"""
DSI Referral Endpoints (Phase 11)

Endpoints for managing underwriter referrals.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..types import (
    ReferralDecision,
    ReferralDecisionType,
    ReferralDetail,
    ReferralListItem,
    QuoteResponse,
    QuoteStatus,
)


logger = logging.getLogger("dsi.api.referrals")

router = APIRouter()


# =============================================================================
# IN-MEMORY STORAGE (Replace with database)
# =============================================================================

_referrals: dict = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def create_mock_referral(referral_id: str) -> dict:
    """Create a mock referral for demonstration."""
    now = datetime.utcnow()

    return {
        "referral_id": referral_id,
        "quote_id": generate_id("quo"),
        "submission_id": generate_id("sub"),
        "entity_name": "Referred Company Inc",
        "coverage": "fi",
        "status": "pending",
        "reasons": ["pricing_review", "large_exposure"],
        "original_tier": 3,
        "original_score": 620,
        "original_premium": 85000,
        "resolved_at": None,
        "resolved_by": None,
        "resolution_notes": [],
        "tier_override": None,
        "premium_adjustment": None,
        "created_at": now - timedelta(hours=4),
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/referrals", response_model=List[ReferralListItem])
async def list_referrals(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, declined)"),
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List referrals with optional filtering.
    """
    # Add mock referrals if empty
    if not _referrals:
        for i in range(5):
            ref_id = generate_id("ref")
            _referrals[ref_id] = create_mock_referral(ref_id)
            if i > 2:
                _referrals[ref_id]["status"] = "approved" if i % 2 == 0 else "declined"

    results = list(_referrals.values())

    # Apply filters
    if status:
        results = [r for r in results if r["status"] == status]

    if coverage:
        results = [r for r in results if r["coverage"] == coverage]

    # Sort by created_at descending
    results.sort(key=lambda r: r["created_at"], reverse=True)

    # Paginate
    results = results[offset:offset + limit]

    return [
        ReferralListItem(
            referral_id=r["referral_id"],
            entity_name=r["entity_name"],
            coverage=r["coverage"],
            status=r["status"],
            reasons=r["reasons"],
            age_hours=(datetime.utcnow() - r["created_at"]).total_seconds() / 3600,
            created_at=r["created_at"],
        )
        for r in results
    ]


@router.get("/referrals/{referral_id}", response_model=ReferralDetail)
async def get_referral(referral_id: str):
    """
    Get referral details by ID.
    """
    if referral_id not in _referrals:
        # Create mock referral for demonstration
        _referrals[referral_id] = create_mock_referral(referral_id)

    r = _referrals[referral_id]

    return ReferralDetail(
        referral_id=r["referral_id"],
        quote_id=r["quote_id"],
        submission_id=r["submission_id"],
        entity_name=r["entity_name"],
        coverage=r["coverage"],
        status=r["status"],
        reasons=r["reasons"],
        original_tier=r["original_tier"],
        original_score=r["original_score"],
        original_premium=r["original_premium"],
        resolved_at=r.get("resolved_at"),
        resolved_by=r.get("resolved_by"),
        resolution_notes=r.get("resolution_notes", []),
        tier_override=r.get("tier_override"),
        premium_adjustment=r.get("premium_adjustment"),
        created_at=r["created_at"],
    )


@router.patch("/referrals/{referral_id}", response_model=ReferralDetail)
async def process_referral(
    referral_id: str,
    decision: ReferralDecision,
):
    """
    Process a referral decision.

    Allows underwriters to approve, decline, or modify the quote.
    """
    if referral_id not in _referrals:
        raise HTTPException(status_code=404, detail="Referral not found")

    r = _referrals[referral_id]

    if r["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Referral already resolved with status: {r['status']}"
        )

    # Process decision
    r["resolved_at"] = datetime.utcnow()
    r["resolved_by"] = decision.underwriter_id or "unknown"
    r["resolution_notes"] = decision.notes

    if decision.decision == ReferralDecisionType.APPROVE:
        r["status"] = "approved"
        if decision.adjustments:
            r["tier_override"] = decision.adjustments.get("tier_override")
            r["premium_adjustment"] = decision.adjustments.get("premium_adjustment")

    elif decision.decision == ReferralDecisionType.DECLINE:
        r["status"] = "declined"

    elif decision.decision == ReferralDecisionType.MODIFY:
        r["status"] = "approved"
        if decision.adjustments:
            r["tier_override"] = decision.adjustments.get("tier_override")
            r["premium_adjustment"] = decision.adjustments.get("premium_adjustment")

    logger.info(
        f"Referral {referral_id} {r['status']} by {r['resolved_by']}"
    )

    return ReferralDetail(
        referral_id=r["referral_id"],
        quote_id=r["quote_id"],
        submission_id=r["submission_id"],
        entity_name=r["entity_name"],
        coverage=r["coverage"],
        status=r["status"],
        reasons=r["reasons"],
        original_tier=r["original_tier"],
        original_score=r["original_score"],
        original_premium=r["original_premium"],
        resolved_at=r["resolved_at"],
        resolved_by=r["resolved_by"],
        resolution_notes=r["resolution_notes"],
        tier_override=r["tier_override"],
        premium_adjustment=r["premium_adjustment"],
        created_at=r["created_at"],
    )


@router.get("/referrals/{referral_id}/quote", response_model=QuoteResponse)
async def get_referral_quote(referral_id: str):
    """
    Get the quote associated with a referral.
    """
    if referral_id not in _referrals:
        raise HTTPException(status_code=404, detail="Referral not found")

    r = _referrals[referral_id]
    now = datetime.utcnow()

    # Calculate adjusted premium if approved with modifications
    premium = r["original_premium"]
    tier = r["original_tier"]

    if r["status"] == "approved":
        if r.get("tier_override"):
            tier = r["tier_override"]
        if r.get("premium_adjustment"):
            premium = premium * r["premium_adjustment"]

    tier_labels = {1: "PREFERRED", 2: "STANDARD", 3: "STANDARD_PLUS", 4: "ELEVATED", 5: "HIGH_RISK"}

    return QuoteResponse(
        quote_id=r["quote_id"],
        submission_id=r["submission_id"],
        status=QuoteStatus.READY if r["status"] == "approved" else QuoteStatus.REFERRED,
        composite_score=r["original_score"],
        tier=tier,
        tier_label=tier_labels.get(tier, "STANDARD"),
        decision="approve" if r["status"] == "approved" else "refer",
        premium_options={
            str(int(premium * 0.5)): premium * 0.5,
            str(int(premium)): premium,
            str(int(premium * 2)): premium * 2,
        },
        recommended_premium=premium,
        referral_reasons=r["reasons"] if r["status"] != "approved" else [],
        referral_id=referral_id if r["status"] == "pending" else None,
        valid_until=now + timedelta(days=30),
        created_at=r["created_at"],
    )


@router.get("/referrals/pending/count")
async def get_pending_count():
    """
    Get count of pending referrals.
    """
    pending = [r for r in _referrals.values() if r["status"] == "pending"]

    return {
        "pending_count": len(pending),
        "oldest_hours": max(
            [(datetime.utcnow() - r["created_at"]).total_seconds() / 3600 for r in pending],
            default=0
        ),
    }


@router.get("/referrals/stats")
async def get_referral_stats():
    """
    Get referral statistics.
    """
    all_refs = list(_referrals.values())

    if not all_refs:
        return {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "declined": 0,
            "approval_rate": 0.0,
            "avg_resolution_hours": 0.0,
        }

    pending = len([r for r in all_refs if r["status"] == "pending"])
    approved = len([r for r in all_refs if r["status"] == "approved"])
    declined = len([r for r in all_refs if r["status"] == "declined"])
    resolved = approved + declined

    # Calculate average resolution time
    resolution_times = []
    for r in all_refs:
        if r.get("resolved_at"):
            delta = (r["resolved_at"] - r["created_at"]).total_seconds() / 3600
            resolution_times.append(delta)

    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0

    return {
        "total": len(all_refs),
        "pending": pending,
        "approved": approved,
        "declined": declined,
        "approval_rate": approved / resolved if resolved > 0 else 0.0,
        "avg_resolution_hours": round(avg_resolution, 1),
    }
