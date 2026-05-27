"""v8.2 broker intelligence endpoints.

  GET /portal/carriers                       -> CarrierRosterResponse
  GET /portal/carriers/{slug}                -> CarrierDetailResponse
  GET /portal/verticals                      -> VerticalListResponse
  GET /portal/client-health                  -> ClientHealthResponse
  GET /portal/placement/{submission_code}    -> PlacementStrategyResponse
  GET /portal/market/pulse                   -> MarketPulseResponse
  GET /portal/market/lines/{line}            -> LineDetailResponse
  GET /portal/book-health                    -> BookHealthResponse
  GET /portal/aggregation                    -> AggregationResponse

Pure aggregation + lookup over existing tables + the hand-crafted
broker_intel_data reference. No new persistence layer.
"""
from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Broker,
    MessageDirection,
    ModelVersionRecord,
    Quote,
    Referral,
    ReferralMessage,
    Submission,
    User,
)

from .broker_intel_data import (
    CARRIER_UNIVERSE,
    CAT_PERILS,
    ESG_VERTICAL_PROFILE,
    MARKET_LINES,
    MARSH_VERTICALS,
    RECENT_LOSS_EVENTS,
    cat_factor,
    engagement_score_for,
    get_carrier,
    get_vertical,
    vertical_for_naics,
)
from .dependencies import get_user_record

router = APIRouter()


# ============================================================================
# Verticals (used by the cross-page filter)
# ============================================================================

class VerticalSummary(BaseModel):
    slug: str
    name: str
    icon: str
    summary: str
    priority_lines: list[str]
    client_count: int = 0
    policy_count: int = 0
    premium_total_usd: float = 0


class VerticalListResponse(BaseModel):
    verticals: list[VerticalSummary]


@router.get("/verticals", response_model=VerticalListResponse)
async def list_verticals(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> VerticalListResponse:
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    # Count clients + premium per vertical from this broker's book
    rows = await db.execute(
        select(Submission, Quote)
        .join(Quote, Quote.submission_id == Submission.id)
        .where(Submission.broker_id == user.broker_id)
    )
    by_vert: dict[str, dict] = {v["slug"]: {"clients": set(), "policies": 0, "premium": 0.0} for v in MARSH_VERTICALS}
    for sub, quote in rows.all():
        sd = sub.submission_data or {}
        naics = sd.get("naics") or sd.get("naics_code")
        slug = vertical_for_naics(naics)
        if slug and slug in by_vert:
            by_vert[slug]["clients"].add(sub.entity_name)
            by_vert[slug]["policies"] += 1
            if quote.recommended_premium:
                by_vert[slug]["premium"] += float(quote.recommended_premium)

    summaries = [
        VerticalSummary(
            slug=v["slug"],
            name=v["name"],
            icon=v["icon"],
            summary=v["summary"],
            priority_lines=v["priority_lines"],
            client_count=len(by_vert[v["slug"]]["clients"]),
            policy_count=by_vert[v["slug"]]["policies"],
            premium_total_usd=by_vert[v["slug"]]["premium"],
        )
        for v in MARSH_VERTICALS
    ]
    return VerticalListResponse(verticals=summaries)


# ============================================================================
# Carriers
# ============================================================================

class CarrierAppetiteEntry(BaseModel):
    coverage: str
    stance: str


class CarrierSummary(BaseModel):
    slug: str
    name: str
    type: str
    headquarters: str
    capacity_band: str
    typical_commission_pct: float
    pricing_position: str
    esg_stance: str
    win_rate: float
    specialties: list[str]
    movement_note: str
    appetite_summary: dict[str, str]


class CarrierRosterResponse(BaseModel):
    carriers: list[CarrierSummary]


class CarrierDetailResponse(BaseModel):
    summary: CarrierSummary
    appetite: list[CarrierAppetiteEntry]
    esg_note: str
    movement_note: str
    # synthesised "your hit rate with this carrier" using win_rate + tiny perturbation
    your_hit_rate_pct: float
    your_premium_placed_usd: float
    your_recent_lines: list[str]


def _carrier_summary(carrier: dict) -> CarrierSummary:
    return CarrierSummary(
        slug=carrier["slug"],
        name=carrier["name"],
        type=carrier["type"],
        headquarters=carrier["headquarters"],
        capacity_band=carrier["capacity_band"],
        typical_commission_pct=carrier["typical_commission_pct"],
        pricing_position=carrier["pricing_position"],
        esg_stance=carrier["esg_stance"],
        win_rate=carrier["win_rate"],
        specialties=carrier["specialties"],
        movement_note=carrier["movement_note"],
        appetite_summary=carrier["appetite"],
    )


@router.get("/carriers", response_model=CarrierRosterResponse)
async def list_carriers(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
) -> CarrierRosterResponse:
    return CarrierRosterResponse(
        carriers=[_carrier_summary(c) for c in CARRIER_UNIVERSE],
    )


@router.get("/carriers/{slug}", response_model=CarrierDetailResponse)
async def carrier_detail(
    slug: str,
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> CarrierDetailResponse:
    carrier = get_carrier(slug)
    if carrier is None:
        raise HTTPException(404, "Carrier not found.")

    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    # Synthesise "your" metrics with this carrier deterministically
    # off win_rate so the demo numbers are stable across renders.
    base_win = carrier["win_rate"]
    your_hit_rate = round(min(0.95, max(0.05, base_win + ((hash(slug) % 11) - 5) * 0.01)), 2)

    # Aggregate broker's premium that could plausibly have been placed
    # with this carrier -- count policies in lines where the carrier
    # leans in or is neutral.
    placed_lines = {
        line for line, stance in carrier["appetite"].items()
        if stance in ("leaning_in", "neutral")
    }
    rows = await db.execute(
        select(Submission, Quote)
        .join(Quote, Quote.submission_id == Submission.id)
        .where(
            Submission.broker_id == user.broker_id,
            Submission.coverage.in_(placed_lines),
        )
    )
    rows_list = list(rows.all())
    # Distribute book premium across all "in" carriers proportional to their win rate.
    in_carriers = [
        c for c in CARRIER_UNIVERSE
        if c["appetite"].get("cyber") in ("leaning_in", "neutral") or True
    ]
    total_winrate_in_book = sum(
        c["win_rate"] for c in in_carriers
        if any(c["appetite"].get(ln) in ("leaning_in", "neutral") for ln in placed_lines)
    ) or 1.0
    book_premium = sum(float(q.recommended_premium or 0) for _, q in rows_list)
    your_premium = round(book_premium * base_win / total_winrate_in_book, 0)

    recent_lines = sorted({sub.coverage for sub, _ in rows_list})

    return CarrierDetailResponse(
        summary=_carrier_summary(carrier),
        appetite=[CarrierAppetiteEntry(coverage=k, stance=v) for k, v in carrier["appetite"].items()],
        esg_note=carrier["esg_note"],
        movement_note=carrier["movement_note"],
        your_hit_rate_pct=your_hit_rate * 100,
        your_premium_placed_usd=your_premium,
        your_recent_lines=recent_lines,
    )


# ============================================================================
# Client health
# ============================================================================

class ClientHealthEntry(BaseModel):
    entity_name: str
    vertical_slug: Optional[str] = None
    vertical_name: Optional[str] = None
    policy_count: int
    total_premium_usd: float
    engagement_score: int
    engagement_label: str
    months_since_last_message: Optional[float] = None
    avg_response_hours: Optional[float] = None
    open_query_count: int
    opportunity_flags: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    next_renewal_in_days: Optional[int] = None


class ClientHealthResponse(BaseModel):
    broker_name: str
    clients: list[ClientHealthEntry]


@router.get("/client-health", response_model=ClientHealthResponse)
async def client_health(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> ClientHealthResponse:
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    broker_q = await db.execute(select(Broker).where(Broker.id == user.broker_id))
    broker = broker_q.scalar_one_or_none()
    if broker is None:
        raise HTTPException(403, "Linked broker not found.")

    # Pull every submission + linked quote for this broker
    rows = await db.execute(
        select(Submission, Quote)
        .join(Quote, Quote.submission_id == Submission.id)
        .where(Submission.broker_id == user.broker_id)
    )
    rows_list = list(rows.all())

    # Group by entity_name
    by_entity: dict[str, list[tuple[Submission, Quote]]] = defaultdict(list)
    for sub, q in rows_list:
        by_entity[sub.entity_name].append((sub, q))

    entries: list[ClientHealthEntry] = []
    now = datetime.now(timezone.utc)

    for entity_name, group in by_entity.items():
        primary = group[0][0]
        sd = primary.submission_data or {}
        naics = sd.get("naics") or sd.get("naics_code")
        vert_slug = vertical_for_naics(naics)
        vert = get_vertical(vert_slug) if vert_slug else None

        total_premium = sum(float(q.recommended_premium or 0) for _, q in group)

        # Get message activity for this entity's referrals
        sub_ids = [s.id for s, _ in group]
        msgs_q = await db.execute(
            select(ReferralMessage)
            .join(Referral, ReferralMessage.referral_id == Referral.id)
            .join(Quote, Referral.quote_id == Quote.id)
            .where(Quote.submission_id.in_(sub_ids))
            .order_by(ReferralMessage.created_at.desc())
        )
        msgs = list(msgs_q.scalars().all())

        last_msg_at = msgs[0].created_at if msgs else None
        months_since_last = None
        if last_msg_at:
            delta_days = (now - last_msg_at.replace(tzinfo=timezone.utc)).days
            months_since_last = round(delta_days / 30.0, 1)

        # Average response time: when a u2b message is followed by b2u,
        # measure the gap. Simplistic but gives a number.
        response_gaps: list[float] = []
        for i in range(len(msgs) - 1):
            cur, prev = msgs[i], msgs[i + 1]
            if cur.direction == MessageDirection.BROKER_TO_UNDERWRITER.value \
               and prev.direction == MessageDirection.UNDERWRITER_TO_BROKER.value:
                gap_hours = (
                    cur.created_at - prev.created_at
                ).total_seconds() / 3600.0
                if 0 < gap_hours < 24 * 60:
                    response_gaps.append(gap_hours)
        avg_response = round(sum(response_gaps) / len(response_gaps), 1) if response_gaps else None

        # Open queries
        open_query_count = sum(
            1 for sub, _ in group
            for ref in await _refs_for_submission(db, sub.id)
            if ref.awaiting_party is not None
        )

        # Recent signal update?
        has_recent_signal = any(m.signal_value_update for m in msgs[:5])

        score, label = engagement_score_for(
            open_query_count=open_query_count,
            avg_response_hours=avg_response,
            months_since_last_message=months_since_last,
            has_recent_signal_update=has_recent_signal,
        )

        # Heuristic opportunity / risk flags
        opportunity, risk = _opportunity_risk_flags(
            entity_name=entity_name,
            group=group,
            vertical_slug=vert_slug,
            engagement_score=score,
        )

        # Synthesise renewal date — 30-180 days out, deterministic per name
        renewal_days = 30 + (abs(hash(entity_name)) % 150)

        entries.append(ClientHealthEntry(
            entity_name=entity_name,
            vertical_slug=vert_slug,
            vertical_name=vert["name"] if vert else None,
            policy_count=len(group),
            total_premium_usd=total_premium,
            engagement_score=score,
            engagement_label=label,
            months_since_last_message=months_since_last,
            avg_response_hours=avg_response,
            open_query_count=open_query_count,
            opportunity_flags=opportunity,
            risk_flags=risk,
            next_renewal_in_days=renewal_days,
        ))

    # Sort by engagement score desc so highest-engagement clients top
    entries.sort(key=lambda e: (-e.engagement_score, e.entity_name))

    return ClientHealthResponse(broker_name=broker.name, clients=entries)


async def _refs_for_submission(db: AsyncSession, submission_id: uuid.UUID) -> list[Referral]:
    q = await db.execute(
        select(Referral).join(Quote, Referral.quote_id == Quote.id).where(
            Quote.submission_id == submission_id
        )
    )
    return list(q.scalars().all())


def _opportunity_risk_flags(
    entity_name: str,
    group: list[tuple[Submission, Quote]],
    vertical_slug: Optional[str],
    engagement_score: int,
) -> tuple[list[str], list[str]]:
    opportunity: list[str] = []
    risk: list[str] = []

    coverages_carried = {sub.coverage for sub, _ in group}

    # Opportunity: missing a coverage their vertical typically carries
    if vertical_slug:
        vert = get_vertical(vertical_slug)
        if vert:
            for line in vert["priority_lines"]:
                if line not in coverages_carried:
                    opportunity.append(f"Missing {line} — typical for {vert['name']}")
                    if len(opportunity) >= 2:
                        break

    # Risk: low engagement
    if engagement_score < 40:
        risk.append("Engagement below healthy threshold")

    # Risk: client interest submission pending (no quote yet)
    for sub, _ in group:
        sd = sub.submission_data or {}
        if sd.get("request_type") in ("client_interest", "broker_recommendation"):
            opportunity.append(f"{sub.coverage} interest awaiting follow-up")
            break

    # Synthesised "growth signal" — deterministic per entity
    if abs(hash(entity_name)) % 3 == 0:
        opportunity.append("Revenue trending up — exposure likely growing")

    # Synthesised CAT exposure for high-CAT verticals
    if vertical_slug in ("manufacturing", "energy-power", "real-estate"):
        if abs(hash(entity_name)) % 4 != 0:
            risk.append("CAT-zone exposure — placement complexity")

    return opportunity[:3], risk[:3]


# ============================================================================
# Placement strategy (per-submission carrier ranking)
# ============================================================================

class CarrierMatch(BaseModel):
    slug: str
    name: str
    suitability_score: int   # 0-100
    appetite_stance: str
    predicted_premium_low: float
    predicted_premium_high: float
    typical_commission_pct: float
    pricing_position: str
    esg_stance: str
    win_rate_pct: float
    rationale: str


class PlacementStrategyResponse(BaseModel):
    submission_code: str
    entity_name: str
    coverage: str
    carrier_matches: list[CarrierMatch]
    placement_note: str


@router.get(
    "/placement/{submission_code}",
    response_model=PlacementStrategyResponse,
)
async def placement_strategy(
    submission_code: str,
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> PlacementStrategyResponse:
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    sub_q = await db.execute(
        select(Submission, Quote).join(Quote, Quote.submission_id == Submission.id)
        .where(
            Submission.submission_code == submission_code,
            Submission.broker_id == user.broker_id,
        )
    )
    row = sub_q.first()
    if row is None:
        raise HTTPException(404, "Submission not found in your book.")

    submission, quote = row
    sd = submission.submission_data or {}
    naics = sd.get("naics") or sd.get("naics_code")
    vert_slug = vertical_for_naics(naics)
    coverage = submission.coverage
    target_premium = float(quote.recommended_premium or 0)

    # Suitability score per carrier: weighted by appetite stance, ESG
    # fit with the vertical, win rate, pricing tightness.
    matches: list[CarrierMatch] = []
    for carrier in CARRIER_UNIVERSE:
        stance = carrier["appetite"].get(coverage, "neutral")
        if stance == "leaning_in":
            base = 75
        elif stance == "neutral":
            base = 55
        elif stance == "selective":
            base = 40
        else:
            base = 20

        # Pricing adjustment
        if carrier["pricing_position"] == "tight":
            base += 10
        elif carrier["pricing_position"] == "light":
            base -= 5

        # ESG match for the vertical
        if vert_slug == "energy-power" and carrier["esg_stance"] == "leader":
            base -= 15  # restrictive on energy
        elif vert_slug == "technology" and carrier["esg_stance"] == "leader":
            base += 5

        # Win rate
        base += int((carrier["win_rate"] - 0.4) * 30)

        # Deterministic jitter so same-stance carriers don't tie
        base += (abs(hash(carrier["slug"] + coverage)) % 7) - 3
        suitability = max(5, min(100, base))

        # Predicted premium range derived from the broker's quote +
        # the carrier's pricing position.
        if carrier["pricing_position"] == "tight":
            lo, hi = target_premium * 0.85, target_premium * 0.95
        elif carrier["pricing_position"] == "light":
            lo, hi = target_premium * 1.05, target_premium * 1.18
        else:
            lo, hi = target_premium * 0.93, target_premium * 1.08

        rationale_parts = [f"Appetite: {stance.replace('_', ' ')}."]
        if carrier["pricing_position"] == "tight":
            rationale_parts.append("Historically tighter pricing than market median.")
        elif carrier["pricing_position"] == "light":
            rationale_parts.append("Wider quoted pricing than market median.")
        if carrier["esg_stance"] == "leader":
            rationale_parts.append("ESG leader — strong fit for sustainability-led insureds.")
        if carrier["typical_commission_pct"] >= 15.0:
            rationale_parts.append(f"Higher commission yield ({carrier['typical_commission_pct']}%).")

        matches.append(CarrierMatch(
            slug=carrier["slug"],
            name=carrier["name"],
            suitability_score=suitability,
            appetite_stance=stance,
            predicted_premium_low=round(lo, 0),
            predicted_premium_high=round(hi, 0),
            typical_commission_pct=carrier["typical_commission_pct"],
            pricing_position=carrier["pricing_position"],
            esg_stance=carrier["esg_stance"],
            win_rate_pct=carrier["win_rate"] * 100,
            rationale=" ".join(rationale_parts),
        ))

    matches.sort(key=lambda m: -m.suitability_score)

    # Build a placement narrative
    top = matches[0] if matches else None
    if top:
        placement_note = (
            f"For this {coverage} placement, lead with {top.name} "
            f"(suitability {top.suitability_score}/100, predicted premium "
            f"${top.predicted_premium_low:,.0f}-${top.predicted_premium_high:,.0f}). "
            f"Consider {matches[1].name} as a secondary market for "
            f"capacity diversity."
        )
    else:
        placement_note = "No carrier matches available."

    return PlacementStrategyResponse(
        submission_code=submission.submission_code,
        entity_name=submission.entity_name,
        coverage=coverage,
        carrier_matches=matches[:8],  # top 8
        placement_note=placement_note,
    )


# ============================================================================
# Market pulse
# ============================================================================

class MarketLineSummary(BaseModel):
    slug: str
    name: str
    cycle_position: str
    rate_change_yoy_pct: float
    capacity_state: str
    capacity_trend: str
    loss_trend: str
    esg_overlay: str


class LossEventEntry(BaseModel):
    headline: str
    line: str
    date: str
    estimated_industry_loss_usd_bn: float
    implication: str


class MarketPulseResponse(BaseModel):
    lines: list[MarketLineSummary]
    recent_loss_events: list[LossEventEntry]
    climate_pulse_summary: str
    cycle_overall: str


class LineDetailResponse(BaseModel):
    slug: str
    name: str
    cycle_position: str
    rate_change_yoy_pct: float
    capacity_state: str
    capacity_trend: str
    loss_trend: str
    summary: str
    key_drivers: list[str]
    esg_overlay: str
    top_carriers: list[CarrierSummary]
    recent_loss_events: list[LossEventEntry]


@router.get("/market/pulse", response_model=MarketPulseResponse)
async def market_pulse(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
) -> MarketPulseResponse:
    lines = [
        MarketLineSummary(
            slug=line["slug"],
            name=line["name"],
            cycle_position=line["cycle_position"],
            rate_change_yoy_pct=line["rate_change_yoy_pct"],
            capacity_state=line["capacity_state"],
            capacity_trend=line["capacity_trend"],
            loss_trend=line["loss_trend"],
            esg_overlay=line["esg_overlay"],
        )
        for line in MARKET_LINES
    ]
    events = [LossEventEntry(**e) for e in RECENT_LOSS_EVENTS]

    # Overall cycle: count hardening vs softening across lines
    hardening = sum(1 for l in MARKET_LINES if l["cycle_position"] == "Hardening")
    softening = sum(1 for l in MARKET_LINES if l["cycle_position"] == "Softening")
    if hardening > softening:
        cycle = "Mixed -> hardening (property + medprof leading)"
    elif softening > hardening:
        cycle = "Mixed -> softening (cyber + D&O leading)"
    else:
        cycle = "Balanced -- bifurcated by line"

    climate = (
        "Climate is the single biggest active force in the broker market today. "
        "Energy capacity is shifting toward renewables on ESG-led withdrawal of "
        "leading carriers; property CAT remains tight after a heavy 2025 season; "
        "ESG governance is now formally part of D&O and FI underwriting questions."
    )

    return MarketPulseResponse(
        lines=lines,
        recent_loss_events=events,
        climate_pulse_summary=climate,
        cycle_overall=cycle,
    )


@router.get("/market/lines/{line}", response_model=LineDetailResponse)
async def market_line_detail(
    line: str,
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
) -> LineDetailResponse:
    line_data = next((l for l in MARKET_LINES if l["slug"] == line), None)
    if line_data is None:
        raise HTTPException(404, "Line not found.")

    # Top carriers for this line by appetite + win rate
    relevant = []
    for c in CARRIER_UNIVERSE:
        stance = c["appetite"].get(line, "neutral")
        if stance in ("leaning_in", "neutral"):
            score = c["win_rate"] + (0.2 if stance == "leaning_in" else 0)
            relevant.append((score, c))
    relevant.sort(key=lambda x: -x[0])
    top_carriers = [_carrier_summary(c) for _, c in relevant[:5]]

    events = [LossEventEntry(**e) for e in RECENT_LOSS_EVENTS if e["line"] == line]

    return LineDetailResponse(
        slug=line_data["slug"],
        name=line_data["name"],
        cycle_position=line_data["cycle_position"],
        rate_change_yoy_pct=line_data["rate_change_yoy_pct"],
        capacity_state=line_data["capacity_state"],
        capacity_trend=line_data["capacity_trend"],
        loss_trend=line_data["loss_trend"],
        summary=line_data["summary"],
        key_drivers=line_data["key_drivers"],
        esg_overlay=line_data["esg_overlay"],
        top_carriers=top_carriers,
        recent_loss_events=events,
    )


# ============================================================================
# Book health
# ============================================================================

class BookHealthResponse(BaseModel):
    broker_name: str
    client_count: int
    policy_count: int
    total_premium_usd: float
    total_estimated_commission_usd: float
    avg_lines_per_client: float
    avg_premium_per_client: float
    retention_rate_pct: float
    cross_sell_ratio_pct: float  # % of clients holding 3+ lines
    avg_tenure_months: float
    lines_concentration: dict[str, int]  # coverage -> policy count
    vertical_concentration: dict[str, int]  # vertical -> policy count
    commission_yield_pct: float


@router.get("/book-health", response_model=BookHealthResponse)
async def book_health(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> BookHealthResponse:
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    broker_q = await db.execute(select(Broker).where(Broker.id == user.broker_id))
    broker = broker_q.scalar_one_or_none()
    if broker is None:
        raise HTTPException(403, "Linked broker not found.")

    rows = await db.execute(
        select(Submission, Quote)
        .join(Quote, Quote.submission_id == Submission.id)
        .where(Submission.broker_id == user.broker_id)
    )
    rows_list = list(rows.all())

    entity_to_lines: dict[str, set[str]] = defaultdict(set)
    line_counts: Counter[str] = Counter()
    vert_counts: Counter[str] = Counter()
    total_premium = 0.0
    total_commission = 0.0

    for sub, q in rows_list:
        entity_to_lines[sub.entity_name].add(sub.coverage)
        line_counts[sub.coverage] += 1
        sd = sub.submission_data or {}
        naics = sd.get("naics") or sd.get("naics_code")
        vert_slug = vertical_for_naics(naics) or "unknown"
        vert_counts[vert_slug] += 1
        premium = float(q.recommended_premium or 0)
        total_premium += premium
        # Average commission of ~13% (book-weighted heuristic).
        total_commission += premium * 0.13

    n_clients = len(entity_to_lines)
    n_policies = sum(len(v) for v in entity_to_lines.values())
    avg_lines = round(n_policies / n_clients, 2) if n_clients else 0
    avg_premium = round(total_premium / n_clients, 0) if n_clients else 0
    cross_sell = round(
        100 * sum(1 for v in entity_to_lines.values() if len(v) >= 3) / max(1, n_clients),
        1,
    )
    commission_yield = round(
        100 * total_commission / total_premium if total_premium else 0,
        1,
    )

    return BookHealthResponse(
        broker_name=broker.name,
        client_count=n_clients,
        policy_count=n_policies,
        total_premium_usd=round(total_premium, 0),
        total_estimated_commission_usd=round(total_commission, 0),
        avg_lines_per_client=avg_lines,
        avg_premium_per_client=avg_premium,
        retention_rate_pct=94.0,   # synthesised; v8.3 measures actual renewals
        cross_sell_ratio_pct=cross_sell,
        avg_tenure_months=37.0,    # synthesised; v8.3 measures actual tenure
        lines_concentration=dict(line_counts),
        vertical_concentration=dict(vert_counts),
        commission_yield_pct=commission_yield,
    )


# ============================================================================
# Risk aggregation
# ============================================================================

class CatPerilExposure(BaseModel):
    peril_slug: str
    peril_name: str
    exposed_policy_count: int
    exposed_premium_usd: float
    relative_severity: float       # 0-1
    most_exposed_verticals: list[str]


class ConcentrationEntry(BaseModel):
    dimension: str
    value: str
    share_pct: float
    count: int
    note: Optional[str] = None


class AggregationResponse(BaseModel):
    broker_name: str
    total_premium_usd: float
    industry_concentration: list[ConcentrationEntry]
    line_concentration: list[ConcentrationEntry]
    cat_peril_exposure: list[CatPerilExposure]
    diversification_score: int
    diversification_note: str


@router.get("/aggregation", response_model=AggregationResponse)
async def risk_aggregation(
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_BROKER_READ)),
    db: AsyncSession = Depends(get_async_db),
) -> AggregationResponse:
    user = await get_user_record(ctx, db)
    if user is None or user.broker_id is None:
        raise HTTPException(403, "Broker identity not configured.")

    broker_q = await db.execute(select(Broker).where(Broker.id == user.broker_id))
    broker = broker_q.scalar_one_or_none()
    if broker is None:
        raise HTTPException(403, "Linked broker not found.")

    rows = await db.execute(
        select(Submission, Quote)
        .join(Quote, Quote.submission_id == Submission.id)
        .where(Submission.broker_id == user.broker_id)
    )
    rows_list = list(rows.all())

    # Premium by vertical + by line
    premium_by_vert: Counter[str] = Counter()
    premium_by_line: Counter[str] = Counter()
    policies_by_vert: Counter[str] = Counter()
    policies_by_line: Counter[str] = Counter()
    submissions_by_vert: dict[str, list[tuple[Submission, Quote]]] = defaultdict(list)

    for sub, q in rows_list:
        sd = sub.submission_data or {}
        naics = sd.get("naics") or sd.get("naics_code")
        vert_slug = vertical_for_naics(naics) or "unknown"
        prem = float(q.recommended_premium or 0)
        premium_by_vert[vert_slug] += prem
        premium_by_line[sub.coverage] += prem
        policies_by_vert[vert_slug] += 1
        policies_by_line[sub.coverage] += 1
        submissions_by_vert[vert_slug].append((sub, q))

    total_premium = sum(premium_by_vert.values())

    industry_entries: list[ConcentrationEntry] = []
    for slug, prem in premium_by_vert.most_common():
        vert = get_vertical(slug)
        industry_entries.append(ConcentrationEntry(
            dimension="industry",
            value=vert["name"] if vert else slug.title(),
            share_pct=round(100 * prem / total_premium, 1) if total_premium else 0,
            count=policies_by_vert[slug],
            note=(
                "High concentration" if total_premium and prem / total_premium > 0.4
                else None
            ),
        ))

    line_entries: list[ConcentrationEntry] = []
    for line, prem in premium_by_line.most_common():
        line_entries.append(ConcentrationEntry(
            dimension="line",
            value=line.title(),
            share_pct=round(100 * prem / total_premium, 1) if total_premium else 0,
            count=policies_by_line[line],
            note=(
                "Single-line dependency" if total_premium and prem / total_premium > 0.5
                else None
            ),
        ))

    # CAT peril exposure: aggregate premium weighted by per-vertical CAT factor
    peril_exposure: list[CatPerilExposure] = []
    for peril in CAT_PERILS:
        exposed_premium = 0.0
        exposed_policies = 0
        per_vert_premium: Counter[str] = Counter()
        for vert_slug, subs in submissions_by_vert.items():
            factor = cat_factor(vert_slug, peril["slug"])
            if factor < 0.4:
                continue
            for sub, q in subs:
                prem = float(q.recommended_premium or 0) * factor
                exposed_premium += prem
                exposed_policies += 1
                per_vert_premium[vert_slug] += prem

        top_verts = [
            get_vertical(s)["name"] if get_vertical(s) else s.title()
            for s, _ in per_vert_premium.most_common(3)
        ]
        relative = (
            round(min(1.0, exposed_premium / total_premium), 2)
            if total_premium else 0
        )

        peril_exposure.append(CatPerilExposure(
            peril_slug=peril["slug"],
            peril_name=peril["name"],
            exposed_policy_count=exposed_policies,
            exposed_premium_usd=round(exposed_premium, 0),
            relative_severity=relative,
            most_exposed_verticals=top_verts,
        ))

    # Diversification: high if industries + lines spread reasonably
    n_verts = len(premium_by_vert)
    n_lines = len(premium_by_line)
    top_industry_share = max(premium_by_vert.values()) / total_premium if total_premium else 1.0
    top_line_share = max(premium_by_line.values()) / total_premium if total_premium else 1.0
    div_score = round(min(100, max(20,
        100 - int(top_industry_share * 50) - int(top_line_share * 30) + (n_verts * 3) + (n_lines * 2)
    )))
    if div_score >= 75:
        div_note = "Well-diversified book across industries and lines."
    elif div_score >= 50:
        div_note = "Moderate diversification — review concentration in dominant industry / line."
    else:
        div_note = "Concentrated book — single industry or line dominates. CAT or sector shock would have disproportionate impact."

    return AggregationResponse(
        broker_name=broker.name,
        total_premium_usd=round(total_premium, 0),
        industry_concentration=industry_entries,
        line_concentration=line_entries,
        cat_peril_exposure=peril_exposure,
        diversification_score=div_score,
        diversification_note=div_note,
    )
