"""
DSI Referral Endpoints (Phase 8/11)

Endpoints for managing underwriter referrals and signal overrides.

Phase 8: Deterministic Referral Management
- Underwriters audit inputs (signals), not outputs (premiums)
- Signal overrides preserve inferred_value, set audited_value
- Model versioning on override (v1=machine, v2+=audited)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body

from ..types import (
    ReferralDecision,
    ReferralDecisionType,
    ReferralDetail,
    ReferralListItem,
    QuoteResponse,
    QuoteStatus,
    SignalOverrideRequest,
    SignalOverrideResponse,
    ReferralSignalDetail,
    ReferralSignalsResponse,
    ModelVersionResponse,
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
        base_premium=r["original_premium"],
        premium_after_modifiers=premium,
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


# =============================================================================
# PHASE 8: SIGNAL OVERRIDE ENDPOINTS (Deterministic Referral Management)
# =============================================================================

# In-memory signal storage (replace with database)
_signal_cache: Dict[str, Dict[str, Any]] = {}
_model_versions: Dict[str, Dict[str, Any]] = {}


def _get_or_create_mock_signals(referral_id: str) -> Dict[str, Any]:
    """Get or create mock signals for a referral."""
    if referral_id not in _signal_cache:
        # Create mock signals for demonstration
        now = datetime.utcnow()
        _signal_cache[referral_id] = {
            "model_version_id": generate_id("mv"),
            "model_version_number": 1,
            "entity_id": f"entity_{referral_id}",
            "signals": {
                "tls_configuration": {
                    "signal_id": "tls_configuration",
                    "signal_name": "TLS Configuration",
                    "group_id": "technical_infrastructure",
                    "group_name": "Technical Infrastructure",
                    "inferred_value": 35.0,
                    "audited_value": None,
                    "is_overridden": False,
                    "weight": 0.15,
                    "confidence": 0.92,
                    "is_flagged": True,
                    "flag_reason": "Score below 40 threshold",
                    "data_sources": ["ssl_labs", "dns_records"],
                    "extracted_at": now - timedelta(hours=2),
                },
                "security_headers": {
                    "signal_id": "security_headers",
                    "signal_name": "Security Headers",
                    "group_id": "technical_infrastructure",
                    "group_name": "Technical Infrastructure",
                    "inferred_value": 45.0,
                    "audited_value": None,
                    "is_overridden": False,
                    "weight": 0.10,
                    "confidence": 0.88,
                    "is_flagged": False,
                    "flag_reason": None,
                    "data_sources": ["http_headers"],
                    "extracted_at": now - timedelta(hours=2),
                },
                "regulatory_compliance": {
                    "signal_id": "regulatory_compliance",
                    "signal_name": "Regulatory Compliance",
                    "group_id": "corporate_governance",
                    "group_name": "Corporate Governance",
                    "inferred_value": 72.0,
                    "audited_value": None,
                    "is_overridden": False,
                    "weight": 0.20,
                    "confidence": 0.95,
                    "is_flagged": False,
                    "flag_reason": None,
                    "data_sources": ["sec_filings", "ofac"],
                    "extracted_at": now - timedelta(hours=2),
                },
                "financial_stability": {
                    "signal_id": "financial_stability",
                    "signal_name": "Financial Stability",
                    "group_id": "corporate_governance",
                    "group_name": "Corporate Governance",
                    "inferred_value": 68.0,
                    "audited_value": None,
                    "is_overridden": False,
                    "weight": 0.25,
                    "confidence": 0.90,
                    "is_flagged": False,
                    "flag_reason": None,
                    "data_sources": ["sec_financials"],
                    "extracted_at": now - timedelta(hours=2),
                },
                "litigation_history": {
                    "signal_id": "litigation_history",
                    "signal_name": "Litigation History",
                    "group_id": "risk_indicators",
                    "group_name": "Risk Indicators",
                    "inferred_value": 28.0,
                    "audited_value": None,
                    "is_overridden": False,
                    "weight": 0.15,
                    "confidence": 0.85,
                    "is_flagged": True,
                    "flag_reason": "Score below 30 indicates significant litigation",
                    "data_sources": ["sec_litigation", "pacer"],
                    "extracted_at": now - timedelta(hours=2),
                },
            },
            "composite_score": 520,
            "tier": 3,
            "tier_label": "STANDARD_PLUS",
        }

        # Store initial model version
        mv_id = _signal_cache[referral_id]["model_version_id"]
        _model_versions[mv_id] = {
            "version_id": mv_id,
            "version_number": 1,
            "version_type": "initial",
            "composite_score": 520,
            "tier": 3,
            "tier_label": "STANDARD_PLUS",
            "confidence": 0.90,
            "signal_count": 5,
            "overridden_signals": [],
            "created_by": "system",
            "created_at": now - timedelta(hours=2),
            "notes": [],
        }

    return _signal_cache[referral_id]


@router.get("/referrals/{referral_id}/signals", response_model=ReferralSignalsResponse)
async def get_referral_signals(
    referral_id: str,
    include_all: bool = Query(False, description="Include all signals, not just flagged"),
):
    """
    Get signals for a referral (Phase 8: Underwriter Signal Review).

    Returns all signals with their inferred values, allowing underwriters
    to review and potentially override machine-inferred values.
    """
    data = _get_or_create_mock_signals(referral_id)

    signals = []
    for sig_data in data["signals"].values():
        # Filter to flagged signals unless include_all
        if not include_all and not sig_data["is_flagged"]:
            continue

        # Calculate contribution to score
        effective_value = sig_data["audited_value"] if sig_data["is_overridden"] else sig_data["inferred_value"]
        contribution = effective_value * sig_data["weight"] * 10  # Contribution to 0-1000 scale

        signals.append(ReferralSignalDetail(
            signal_id=sig_data["signal_id"],
            signal_name=sig_data["signal_name"],
            group_id=sig_data["group_id"],
            group_name=sig_data["group_name"],
            inferred_value=sig_data["inferred_value"],
            audited_value=sig_data["audited_value"],
            is_overridden=sig_data["is_overridden"],
            weight=sig_data["weight"],
            contribution_to_score=contribution,
            is_flagged=sig_data["is_flagged"],
            flag_reason=sig_data["flag_reason"],
            confidence=sig_data["confidence"],
            data_sources=sig_data["data_sources"],
            extracted_at=sig_data["extracted_at"],
        ))

    flagged_count = len([s for s in data["signals"].values() if s["is_flagged"]])
    overridden_count = len([s for s in data["signals"].values() if s["is_overridden"]])
    avg_confidence = sum(s["confidence"] for s in data["signals"].values()) / len(data["signals"])

    return ReferralSignalsResponse(
        referral_id=referral_id,
        model_version_id=data["model_version_id"],
        signals=signals,
        flagged_count=flagged_count,
        overridden_count=overridden_count,
        total_signals=len(data["signals"]),
        signal_coverage=1.0,  # All signals extracted
        average_confidence=avg_confidence,
    )


@router.post("/referrals/{referral_id}/signals/override", response_model=SignalOverrideResponse)
async def override_signal(
    referral_id: str,
    override: SignalOverrideRequest,
):
    """
    Override a signal value during referral review (Phase 8).

    This is the core Phase 8 operation: underwriters audit inputs (signals),
    not outputs (premiums). The formula remains pure.

    - inferred_value is PRESERVED (permanent machine view)
    - audited_value is SET (mutable human override)
    - A new model version is created (v1=machine, v2+=audited)
    - Score is recalculated using audited_value
    """
    data = _get_or_create_mock_signals(referral_id)

    # Validate signal exists
    if override.signal_id not in data["signals"]:
        raise HTTPException(
            status_code=404,
            detail=f"Signal '{override.signal_id}' not found in referral"
        )

    signal = data["signals"][override.signal_id]
    old_model_version_id = data["model_version_id"]

    # Store previous values for impact calculation
    old_effective = signal["audited_value"] if signal["is_overridden"] else signal["inferred_value"]
    old_composite = data["composite_score"]
    old_tier = data["tier"]

    # Apply override (Phase 8: preserve inferred_value, set audited_value)
    signal["audited_value"] = override.audited_value
    signal["is_overridden"] = True

    # Recalculate composite score
    new_composite = 0.0
    for sig in data["signals"].values():
        effective = sig["audited_value"] if sig["is_overridden"] else sig["inferred_value"]
        new_composite += effective * sig["weight"] * 10  # 0-1000 scale

    data["composite_score"] = new_composite

    # Determine new tier based on score
    tier_bands = [(800, 1), (650, 2), (500, 3), (350, 4), (0, 5)]
    new_tier = 5
    for threshold, tier in tier_bands:
        if new_composite >= threshold:
            new_tier = tier
            break

    tier_labels = {1: "PREFERRED", 2: "STANDARD", 3: "STANDARD_PLUS", 4: "ELEVATED", 5: "HIGH_RISK"}
    data["tier"] = new_tier
    data["tier_label"] = tier_labels[new_tier]

    # Create new model version (Phase 8: v1=machine, v2+=audited)
    new_version_number = data["model_version_number"] + 1
    new_model_version_id = generate_id("mv")
    data["model_version_id"] = new_model_version_id
    data["model_version_number"] = new_version_number

    now = datetime.utcnow()
    underwriter_id = override.underwriter_id or "unknown"

    _model_versions[new_model_version_id] = {
        "version_id": new_model_version_id,
        "version_number": new_version_number,
        "version_type": "signal_override",
        "composite_score": new_composite,
        "tier": new_tier,
        "tier_label": tier_labels[new_tier],
        "confidence": sum(s["confidence"] for s in data["signals"].values()) / len(data["signals"]),
        "signal_count": len(data["signals"]),
        "overridden_signals": [s["signal_id"] for s in data["signals"].values() if s["is_overridden"]],
        "created_by": underwriter_id,
        "created_at": now,
        "notes": [f"Signal '{override.signal_id}' overridden: {signal['inferred_value']:.0f} -> {override.audited_value:.0f}"],
    }

    # Calculate impact
    score_impact = new_composite - old_composite
    tier_impact = new_tier - old_tier

    logger.info(
        f"Signal override on referral {referral_id}: "
        f"{override.signal_id} {signal['inferred_value']:.0f} -> {override.audited_value:.0f}, "
        f"score impact: {score_impact:+.0f}, tier impact: {tier_impact:+d}"
    )

    return SignalOverrideResponse(
        signal_id=override.signal_id,
        entity_id=data["entity_id"],
        model_version_id=new_model_version_id,
        inferred_value=signal["inferred_value"],
        audited_value=override.audited_value,
        score_impact=score_impact,
        tier_impact=tier_impact,
        new_composite_score=new_composite,
        new_tier=new_tier,
        new_tier_label=tier_labels[new_tier],
        overridden_by=underwriter_id,
        overridden_at=now,
        rationale=override.rationale,
        evidence_reference=override.evidence_reference,
        previous_model_version=old_model_version_id,
        new_model_version=new_model_version_id,
    )


@router.get("/referrals/{referral_id}/model-versions", response_model=List[ModelVersionResponse])
async def get_model_versions(referral_id: str):
    """
    Get model version history for a referral (Phase 8 audit trail).

    Shows the progression from v1 (machine view) through v2+ (audited views).
    """
    data = _get_or_create_mock_signals(referral_id)

    # Collect all versions related to this referral
    versions = []
    for mv_id, mv in _model_versions.items():
        # Simple check - in production this would be a proper relationship
        if mv["version_number"] <= data["model_version_number"]:
            versions.append(ModelVersionResponse(
                version_id=mv["version_id"],
                version_number=mv["version_number"],
                version_type=mv["version_type"],
                composite_score=mv["composite_score"],
                tier=mv["tier"],
                tier_label=mv["tier_label"],
                confidence=mv["confidence"],
                signal_count=mv["signal_count"],
                overridden_signals=mv["overridden_signals"],
                created_by=mv["created_by"],
                created_at=mv["created_at"],
                notes=mv["notes"],
            ))

    # Sort by version number
    versions.sort(key=lambda v: v.version_number)

    return versions


@router.delete("/referrals/{referral_id}/signals/{signal_id}/override")
async def revert_signal_override(
    referral_id: str,
    signal_id: str,
    underwriter_id: Optional[str] = Query(None),
):
    """
    Revert a signal override back to machine-inferred value.

    Creates a new model version documenting the reversion.
    """
    data = _get_or_create_mock_signals(referral_id)

    if signal_id not in data["signals"]:
        raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")

    signal = data["signals"][signal_id]

    if not signal["is_overridden"]:
        raise HTTPException(status_code=400, detail=f"Signal '{signal_id}' is not overridden")

    # Revert
    old_audited = signal["audited_value"]
    signal["audited_value"] = None
    signal["is_overridden"] = False

    # Recalculate composite
    new_composite = 0.0
    for sig in data["signals"].values():
        effective = sig["audited_value"] if sig["is_overridden"] else sig["inferred_value"]
        new_composite += effective * sig["weight"] * 10

    data["composite_score"] = new_composite

    # Determine tier
    tier_bands = [(800, 1), (650, 2), (500, 3), (350, 4), (0, 5)]
    new_tier = 5
    for threshold, tier in tier_bands:
        if new_composite >= threshold:
            new_tier = tier
            break

    tier_labels = {1: "PREFERRED", 2: "STANDARD", 3: "STANDARD_PLUS", 4: "ELEVATED", 5: "HIGH_RISK"}
    data["tier"] = new_tier
    data["tier_label"] = tier_labels[new_tier]

    # Create new model version
    new_version_number = data["model_version_number"] + 1
    new_model_version_id = generate_id("mv")
    data["model_version_id"] = new_model_version_id
    data["model_version_number"] = new_version_number

    now = datetime.utcnow()
    _model_versions[new_model_version_id] = {
        "version_id": new_model_version_id,
        "version_number": new_version_number,
        "version_type": "override_reverted",
        "composite_score": new_composite,
        "tier": new_tier,
        "tier_label": tier_labels[new_tier],
        "confidence": sum(s["confidence"] for s in data["signals"].values()) / len(data["signals"]),
        "signal_count": len(data["signals"]),
        "overridden_signals": [s["signal_id"] for s in data["signals"].values() if s["is_overridden"]],
        "created_by": underwriter_id or "unknown",
        "created_at": now,
        "notes": [f"Override reverted for '{signal_id}': {old_audited:.0f} -> {signal['inferred_value']:.0f} (machine)"],
    }

    logger.info(f"Signal override reverted on referral {referral_id}: {signal_id}")

    return {
        "status": "reverted",
        "signal_id": signal_id,
        "reverted_to": signal["inferred_value"],
        "new_composite_score": new_composite,
        "new_tier": new_tier,
        "new_model_version": new_model_version_id,
    }
