"""v8.1 portal endpoints:

  GET  /portal/profile                 -> ClientProfileResponse (CLIENT)
  POST /portal/coverage-requests       -> CoverageRequestResponse (CLIENT)
  GET  /portal/recommendations         -> BrokerRecommendationsResponse (BROKER)
  POST /portal/recommendations/send    -> push recommendation to client (BROKER)

The recommendations endpoints are intentionally rule-based for the
demo -- no LLM, no ML, just simple coverage-gap heuristics over the
broker's book. Easy to inspect, easy to defend in a pitch.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Broker,
    DecisionType,
    MessageDirection,
    ModelVersionRecord,
    Quote,
    Referral,
    ReferralMessage,
    ReferralStatus,
    Submission,
    SubmissionStatus,
    User,
)

from .dependencies import get_user_record, require_portal_user

router = APIRouter()


async def _new_interest_submission(
    db: AsyncSession,
    *,
    entity_name: str,
    coverage: str,
    broker_id: Optional[uuid.UUID],
    created_by_user_id: uuid.UUID,
    submission_data: dict,
    recommended_limit: Optional[float],
) -> tuple[Submission, Quote]:
    """Shared helper for client-interest and broker-recommendation
    requests. Creates a placeholder Submission + stub ModelVersion +
    Quote so the schema's NOT NULL Quote.model_version_id constraint
    is honoured even though the request hasn't been scored yet.

    The stub ModelVersion has no scoring data on it -- it exists
    purely so the Quote -> Referral chain has somewhere to anchor.
    """
    from infrastructure.db.repositories import generate_id

    now = datetime.now(timezone.utc)

    submission = Submission(
        submission_code=generate_id("sub"),
        entity_name=entity_name,
        coverage=coverage,
        configuration=f"{coverage}_general",
        status=SubmissionStatus.PENDING,
        submission_data=submission_data,
        direct_query_responses={},
        broker_id=broker_id,
        created_by=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(submission)
    await db.flush()

    mv = ModelVersionRecord(
        version_code=generate_id("mv"),
        submission_id=submission.id,
        version_number=1,
        version_type="interest",
        is_latest=True,
        config_hash="interest",
        coverage=coverage,
        configuration_name=f"{coverage}_general",
        created_at=now,
    )
    db.add(mv)
    await db.flush()

    quote = Quote(
        quote_code=generate_id("quo"),
        submission_id=submission.id,
        model_version_id=mv.id,
        recommended_premium=None,
        recommended_limit=recommended_limit,
        created_at=now,
        updated_at=now,
    )
    db.add(quote)
    await db.flush()

    return submission, quote


# ============================================================================
# Profile (CLIENT)
# ============================================================================

class ClientProfileResponse(BaseModel):
    entity_name: str
    broker_name: Optional[str] = None
    industry_code: Optional[str] = None
    industry_label: Optional[str] = None
    revenue_band: Optional[str] = None
    revenue: Optional[float] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    naics_code: Optional[str] = None
    active_coverage_count: int = 0
    coverage_lines: list[str] = Field(default_factory=list)
    # Signal categories grouped by whether we have observed data
    # (i.e. at least one model_version_signal under that group)
    signal_categories_observed: list[str] = Field(default_factory=list)
    signal_categories_pending: list[str] = Field(default_factory=list)


# Mapping from NAICS 2-digit section to human-readable label. Only the
# sections we expect in the demo are populated; others fall through to
# the raw code.
_NAICS_LABELS: dict[str, str] = {
    "11": "Agriculture, Forestry, Fishing",
    "21": "Mining, Quarrying, Oil & Gas",
    "22": "Utilities",
    "23": "Construction",
    "31": "Manufacturing",
    "32": "Manufacturing",
    "33": "Manufacturing",
    "42": "Wholesale Trade",
    "44": "Retail Trade",
    "45": "Retail Trade",
    "48": "Transportation & Warehousing",
    "49": "Transportation & Warehousing",
    "51": "Information",
    "52": "Finance & Insurance",
    "53": "Real Estate & Rental",
    "54": "Professional & Technical Services",
    "55": "Management of Companies",
    "56": "Administrative & Support",
    "61": "Educational Services",
    "62": "Healthcare & Social Assistance",
    "71": "Arts, Entertainment & Recreation",
    "72": "Accommodation & Food Services",
    "81": "Other Services",
    "92": "Public Administration",
}


# Standard signal category groups we surface. Static for demo; in
# production this would derive from the active coverage configs.
_STANDARD_CATEGORIES: list[str] = [
    "Network Authority",
    "Technical Infrastructure",
    "Asset Telemetry",
    "Structured Data",
    "Corporate Footprint",
    "Public Records",
    "Direct Inquiry",
]


@router.get("/profile", response_model=ClientProfileResponse)
async def client_profile(
    ctx: AuthContext = Depends(require_portal_user),
    db: AsyncSession = Depends(get_async_db),
) -> ClientProfileResponse:
    """Aggregate entity-level profile for the authenticated client.

    Brokers don't have a single "profile" -- they have a book of
    clients -- so this endpoint is CLIENT-only. Returns the entity
    identity, jurisdiction, industry, and a high-level signal census.
    """
    if ctx.role != "CLIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile view is for client users only.",
        )

    user = await get_user_record(ctx, db)
    if user is None or user.tenant_id is None:
        raise HTTPException(403, "User record not found.")

    # All submissions in this client tenant (created by anyone in the
    # tenant, not just this user)
    user_ids_q = await db.execute(
        select(User.id).where(User.tenant_id == user.tenant_id)
    )
    user_ids = [row[0] for row in user_ids_q.all()]
    if not user_ids:
        raise HTTPException(404, "No submissions found.")

    subs_q = await db.execute(
        select(Submission).where(Submission.created_by.in_(user_ids))
    )
    submissions = list(subs_q.scalars().all())
    if not submissions:
        raise HTTPException(404, "No submissions found.")

    primary = submissions[0]
    submission_data = primary.submission_data if isinstance(primary.submission_data, dict) else {}

    naics_code = (
        submission_data.get("naics")
        or submission_data.get("naics_code")
        or submission_data.get("NAICS")
    )
    if naics_code is not None:
        naics_code = str(naics_code)
    industry_code = naics_code[:2] if naics_code and len(naics_code) >= 2 else None
    industry_label = _NAICS_LABELS.get(industry_code or "", industry_code)

    revenue = submission_data.get("revenue") or submission_data.get("annual_revenue")
    try:
        revenue_f = float(revenue) if revenue is not None else None
    except (ValueError, TypeError):
        revenue_f = None
    revenue_band = _revenue_band(revenue_f) if revenue_f is not None else None

    broker_name: Optional[str] = None
    if primary.broker_id is not None:
        broker_q = await db.execute(
            select(Broker).where(Broker.id == primary.broker_id)
        )
        broker = broker_q.scalar_one_or_none()
        if broker:
            broker_name = broker.name

    # Signal census: which signal categories has the workflow observed
    # at least once across this entity's coverages? For the demo we
    # don't have a clean category-name mapping wired through the API,
    # so we use a heuristic: count the modifier_applied entries on the
    # primary submission's latest model_version and classify by source.
    observed: set[str] = set()
    mv_q = await db.execute(
        select(ModelVersionRecord).where(
            ModelVersionRecord.submission_id == primary.id,
            ModelVersionRecord.is_latest == True,  # noqa: E712
        )
    )
    mv = mv_q.scalar_one_or_none()
    if mv and isinstance(mv.modifiers_applied, list):
        for m in mv.modifiers_applied:
            if isinstance(m, dict):
                src = (m.get("source") or "").lower()
                if src == "direct_query":
                    observed.add("Direct Inquiry")
                elif src == "categorical":
                    observed.add("Corporate Footprint")
                else:
                    observed.add("Technical Infrastructure")
    # Treat industry / size signals as always observed if we have
    # NAICS + revenue
    if industry_code:
        observed.add("Corporate Footprint")
    if revenue_band:
        observed.add("Public Records")

    pending = [c for c in _STANDARD_CATEGORIES if c not in observed]

    return ClientProfileResponse(
        entity_name=primary.entity_name,
        broker_name=broker_name,
        industry_code=industry_code,
        industry_label=industry_label,
        revenue_band=revenue_band,
        revenue=revenue_f,
        domain=primary.discovered_domain or primary.domain_hint,
        country=primary.country_hint,
        naics_code=naics_code,
        active_coverage_count=len(submissions),
        coverage_lines=sorted({s.coverage for s in submissions}),
        signal_categories_observed=sorted(observed),
        signal_categories_pending=pending,
    )


def _revenue_band(revenue: float) -> str:
    if revenue < 10_000_000: return "<10M"
    if revenue < 50_000_000: return "10-50M"
    if revenue < 250_000_000: return "50-250M"
    if revenue < 1_000_000_000: return "250M-1B"
    return ">1B"


# ============================================================================
# Coverage requests (CLIENT)
# ============================================================================

class CoverageRequestPayload(BaseModel):
    coverage: str = Field(..., min_length=1, max_length=64)
    desired_limit: Optional[float] = Field(default=None, ge=0)
    desired_effective_date: Optional[str] = None
    rationale: str = Field(default="", max_length=4000)


class CoverageRequestResponse(BaseModel):
    request_code: str
    submission_code: str
    referral_code: str
    status: str = "submitted"


@router.post(
    "/coverage-requests",
    response_model=CoverageRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_coverage(
    payload: CoverageRequestPayload,
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_CLIENT_SUBMIT)),
    db: AsyncSession = Depends(get_async_db),
) -> CoverageRequestResponse:
    """Client-initiated coverage interest. Creates a placeholder
    submission with PENDING status, opens a referral on it, and posts
    a single client-to-broker message describing the interest. The
    broker sees this in their Communications inbox immediately.
    """
    from infrastructure.db.repositories import generate_id

    user = await get_user_record(ctx, db)
    if user is None:
        raise HTTPException(403, "User record not found.")

    # Find the user's primary broker (from an existing submission).
    sib_q = await db.execute(
        select(Submission)
        .where(Submission.created_by == user.id)
        .limit(1)
    )
    sibling = sib_q.scalar_one_or_none()
    broker_id = sibling.broker_id if sibling else None
    entity_name = sibling.entity_name if sibling else (user.full_name or "Client")

    now = datetime.now(timezone.utc)

    submission, quote = await _new_interest_submission(
        db,
        entity_name=entity_name,
        coverage=payload.coverage,
        broker_id=broker_id,
        created_by_user_id=user.id,
        submission_data={
            "request_type": "client_interest",
            "desired_limit": payload.desired_limit,
            "desired_effective_date": payload.desired_effective_date,
            "rationale": payload.rationale,
        },
        recommended_limit=payload.desired_limit,
    )

    referral = Referral(
        referral_code=generate_id("ref"),
        quote_id=quote.id,
        status=ReferralStatus.PENDING,
        awaiting_party="broker",
        reasons=[f"Client interest in {payload.coverage} coverage"],
        priority=4,
        created_at=now,
        updated_at=now,
    )
    db.add(referral)
    await db.flush()

    # First message in the thread -- from the client side. We use
    # BROKER_TO_UNDERWRITER direction here as the closest semantic
    # fit for the existing two-direction enum (broker = "client side"
    # in the v8 model). v8.2 could add CLIENT_TO_BROKER explicitly.
    initial_body = (
        f"I'd like to explore {payload.coverage} coverage."
        + (f" Target limit: ${payload.desired_limit:,.0f}." if payload.desired_limit else "")
        + (f" Preferred effective: {payload.desired_effective_date}." if payload.desired_effective_date else "")
        + (f"\n\n{payload.rationale}" if payload.rationale.strip() else "")
    )
    db.add(ReferralMessage(
        referral_id=referral.id,
        direction=MessageDirection.BROKER_TO_UNDERWRITER.value,
        author_user_id=user.id,
        body=initial_body,
        created_at=now,
    ))

    await db.commit()

    return CoverageRequestResponse(
        request_code=submission.submission_code,
        submission_code=submission.submission_code,
        referral_code=referral.referral_code,
    )


# ============================================================================
# Broker recommendations
# ============================================================================

class BookGapRecommendation(BaseModel):
    client_entity_name: str
    coverage: str
    rationale: str
    estimated_premium_range_usd: tuple[float, float]
    industry_label: Optional[str] = None


class BrokerRecommendationsResponse(BaseModel):
    broker_name: str
    recommendations: list[BookGapRecommendation] = Field(default_factory=list)


# Default "every business should have these" coverages per industry
# section. Used as the rule-base for gap analysis. Easy to inspect /
# defend in a pitch; not pretending to be ML.
_INDUSTRY_EXPECTED_COVERAGES: dict[str, list[str]] = {
    # Information / tech
    "51": ["cyber", "pi", "do", "property"],
    # Healthcare
    "62": ["cyber", "medprof", "pi", "property"],
    # Manufacturing
    "31": ["cyber", "casualty", "prodlib", "property"],
    "32": ["cyber", "casualty", "prodlib", "property"],
    "33": ["cyber", "casualty", "prodlib", "property"],
    # Construction
    "23": ["casualty", "property", "do"],
    # Default fallback for any other section
    "_default": ["cyber", "casualty", "property", "do"],
}

# Heuristic premium-range table by (coverage, revenue band).
# Per-entity numbers; tuned to feel credible in a demo. Real
# placement involves underwriting -- these are conversation starters.
_HEURISTIC_PREMIUM_RANGES: dict[tuple[str, str], tuple[float, float]] = {
    ("cyber", "<10M"):       (8_000,   18_000),
    ("cyber", "10-50M"):     (25_000,  60_000),
    ("cyber", "50-250M"):    (75_000,  220_000),
    ("cyber", "250M-1B"):    (180_000, 480_000),
    ("cyber", ">1B"):        (350_000, 1_200_000),
    ("pi",    "<10M"):       (6_000,   14_000),
    ("pi",    "10-50M"):     (18_000,  40_000),
    ("pi",    "50-250M"):    (45_000,  110_000),
    ("pi",    "250M-1B"):    (95_000,  280_000),
    ("pi",    ">1B"):        (220_000, 700_000),
    ("do",    "<10M"):       (12_000,  28_000),
    ("do",    "10-50M"):     (40_000,  90_000),
    ("do",    "50-250M"):    (100_000, 250_000),
    ("do",    "250M-1B"):    (220_000, 550_000),
    ("do",    ">1B"):        (500_000, 1_400_000),
    ("property","<10M"):     (10_000,  25_000),
    ("property","10-50M"):   (35_000,  85_000),
    ("property","50-250M"):  (70_000,  220_000),
    ("property","250M-1B"):  (160_000, 480_000),
    ("property",">1B"):      (380_000, 1_100_000),
    ("casualty","<10M"):     (15_000,  35_000),
    ("casualty","10-50M"):   (50_000,  120_000),
    ("casualty","50-250M"):  (130_000, 320_000),
    ("casualty","250M-1B"):  (280_000, 720_000),
    ("casualty",">1B"):      (650_000, 1_800_000),
    ("medprof","50-250M"):   (140_000, 380_000),
    ("medprof","10-50M"):    (60_000,  160_000),
    ("prodlib","50-250M"):   (95_000,  250_000),
    ("prodlib","250M-1B"):   (220_000, 580_000),
}


def _estimate_premium_range(coverage: str, revenue_band: str) -> tuple[float, float]:
    key = (coverage, revenue_band)
    return _HEURISTIC_PREMIUM_RANGES.get(key, (50_000, 150_000))


@router.get("/recommendations", response_model=BrokerRecommendationsResponse)
async def broker_recommendations(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> BrokerRecommendationsResponse:
    """Rule-based coverage-gap analysis across the broker's book."""
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    broker_q = await db.execute(select(Broker).where(Broker.id == user.broker_id))
    broker = broker_q.scalar_one_or_none()
    if broker is None:
        raise HTTPException(403, "Linked broker not found.")

    subs_q = await db.execute(
        select(Submission).where(Submission.broker_id == user.broker_id)
    )
    submissions = list(subs_q.scalars().all())

    # Group submissions by entity_name (lowercased) so we know what
    # coverages each entity already carries.
    by_entity: dict[str, list[Submission]] = {}
    for s in submissions:
        key = (s.entity_name or "").strip().lower()
        by_entity.setdefault(key, []).append(s)

    recommendations: list[BookGapRecommendation] = []
    for entity_key, group in by_entity.items():
        primary = group[0]
        sd = primary.submission_data if isinstance(primary.submission_data, dict) else {}
        naics = (sd.get("naics") or sd.get("naics_code") or "")
        naics_section = str(naics)[:2] if naics else ""
        industry_label = _NAICS_LABELS.get(naics_section)
        revenue = sd.get("revenue") or sd.get("annual_revenue") or 0
        try:
            rev_band = _revenue_band(float(revenue))
        except (TypeError, ValueError):
            rev_band = "50-250M"

        expected = _INDUSTRY_EXPECTED_COVERAGES.get(
            naics_section, _INDUSTRY_EXPECTED_COVERAGES["_default"],
        )
        carried = {s.coverage for s in group}
        gaps = [c for c in expected if c not in carried]

        for gap in gaps:
            lo, hi = _estimate_premium_range(gap, rev_band)
            rationale = (
                f"{primary.entity_name} carries "
                f"{', '.join(sorted(carried)) or 'no coverage'} but has no "
                f"{gap}. {industry_label or 'Entities in this industry'} of "
                f"similar size typically place {gap} at "
                f"${lo:,.0f}-${hi:,.0f}."
            )
            recommendations.append(BookGapRecommendation(
                client_entity_name=primary.entity_name,
                coverage=gap,
                rationale=rationale,
                estimated_premium_range_usd=(lo, hi),
                industry_label=industry_label,
            ))

    return BrokerRecommendationsResponse(
        broker_name=broker.name,
        recommendations=recommendations,
    )


class SendRecommendationPayload(BaseModel):
    client_entity_name: str = Field(..., min_length=1)
    coverage: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4000)


class SendRecommendationResponse(BaseModel):
    submission_code: str
    referral_code: str
    status: str = "sent"


@router.post(
    "/recommendations/send",
    response_model=SendRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_recommendation(
    payload: SendRecommendationPayload,
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_REPLY)),
    db: AsyncSession = Depends(get_async_db),
) -> SendRecommendationResponse:
    """Broker pushes a recommendation to one of their clients via the
    Communications channel. Creates a placeholder submission +
    referral + initial broker-side message, just like client coverage
    requests, so the conversation appears in the client's inbox.
    """
    from infrastructure.db.repositories import generate_id

    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    # Find any existing submission for this client+broker so we can
    # mirror its identity onto the new placeholder.
    sub_q = await db.execute(
        select(Submission)
        .where(
            Submission.broker_id == user.broker_id,
            Submission.entity_name == payload.client_entity_name,
        )
        .limit(1)
    )
    existing = sub_q.scalar_one_or_none()
    if existing is None:
        raise HTTPException(404, "Client not found in your book.")

    now = datetime.now(timezone.utc)

    submission, quote = await _new_interest_submission(
        db,
        entity_name=existing.entity_name,
        coverage=payload.coverage,
        broker_id=user.broker_id,
        created_by_user_id=user.id,
        submission_data={
            "request_type": "broker_recommendation",
            "rationale": payload.message,
            "naics": (existing.submission_data or {}).get("naics"),
            "revenue": (existing.submission_data or {}).get("revenue"),
        },
        recommended_limit=None,
    )

    referral = Referral(
        referral_code=generate_id("ref"),
        quote_id=quote.id,
        status=ReferralStatus.PENDING,
        awaiting_party="client",
        reasons=[f"Broker recommendation: {payload.coverage}"],
        priority=4,
        created_at=now,
        updated_at=now,
    )
    db.add(referral)
    await db.flush()

    db.add(ReferralMessage(
        referral_id=referral.id,
        direction=MessageDirection.UNDERWRITER_TO_BROKER.value,  # broker as sender, client as recipient
        author_user_id=user.id,
        body=payload.message,
        created_at=now,
    ))

    await db.commit()

    return SendRecommendationResponse(
        submission_code=submission.submission_code,
        referral_code=referral.referral_code,
    )
