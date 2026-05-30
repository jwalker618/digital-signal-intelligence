"""v8 Phase 6: response schemas for the portal API.

These compose Phase 2/3/4 Pydantic models into the response envelopes
the frontend consumes. No new logic -- just shaping.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from layers.cohort.service import CohortStats, SignalRanking
from layers.risk.impact_breakdown import ImpactBreakdown
from layers.risk.remediation import RemediationPlan


# -----------------------------------------------------------------------------
# /portal/overview
# -----------------------------------------------------------------------------

class BrokerInfo(BaseModel):
    id: str
    name: str
    slug: str


class ClientBookEntry(BaseModel):
    """One row in the broker's book-of-clients view."""
    submission_code: str
    entity_name: str
    coverage: str
    status: str
    composite_score: Optional[float] = None
    tier: Optional[int] = None
    peer_percentile_rank: Optional[float] = None
    recommended_premium: Optional[float] = None
    referral_state: Optional[str] = None
    awaiting_party: Optional[str] = None
    updated_at: Optional[datetime] = None
    # Practice vertical, derived from the submission's NAICS section. Powers
    # the book-roster quick-filter chips. Null when NAICS is unavailable.
    vertical: Optional[str] = None        # slug, e.g. "energy-power"
    vertical_name: Optional[str] = None   # display, e.g. "Energy & Power"


class BrokerOverviewResponse(BaseModel):
    role: str = "BROKER"
    broker: BrokerInfo
    clients: list[ClientBookEntry] = Field(default_factory=list)
    open_queries_count: int = 0


class ScoreHistoryPoint(BaseModel):
    """One historical model_version score for the client overview sparkline.

    Sorted oldest -> newest by the builder. Population is best-effort: a
    submission's score history may be shorter than the requested window.
    """
    version_number: int
    composite_score: float
    created_at: datetime


class ClientCoverageEntry(BaseModel):
    submission_code: str
    coverage: str
    composite_score: Optional[float] = None
    tier: Optional[int] = None
    peer_percentile_rank: Optional[float] = None
    recommended_premium: Optional[float] = None
    referral_state: Optional[str] = None
    updated_at: Optional[datetime] = None
    # Phase B1: peer cohort + score history + exposure context so the
    # Client Summary page can render real values in place of the
    # design-default placeholders. All optional -- absent when the latest
    # MV row is missing or the cohort is too thin to summarise.
    peer_cohort_median_score: Optional[float] = None
    peer_cohort_size: Optional[int] = None
    peer_cohort_top_decile: Optional[float] = None
    peer_cohort_min: Optional[float] = None
    peer_cohort_max: Optional[float] = None
    previous_composite_score: Optional[float] = None
    score_history: Optional[list[ScoreHistoryPoint]] = None
    exposure_value: Optional[float] = None
    exposure_band_label: Optional[str] = None
    exposure_size_score: Optional[float] = None
    exposure_value_prior: Optional[float] = None
    # Phase B2: loss-outlook summary off the latest MV row so the
    # LossOutlookCard renders the real band / trend / velocities, plus
    # a 12-quarter incurred-loss strip aggregated from loss_events
    # (oldest-first, normalised so max=1.0). All optional.
    loss_propensity_band: Optional[str] = None
    loss_trend_direction: Optional[str] = None
    loss_frequency_velocity: Optional[float] = None
    loss_severity_velocity: Optional[float] = None
    loss_event_quarters: Optional[list[float]] = None
    # Phase F.2: policy facts for the Coverages table (limit / retention /
    # aggregate / expiry). Carrier name has no DB source — omitted.
    limit: Optional[float] = None
    deductible: Optional[float] = None
    aggregate_limit: Optional[float] = None
    expires_at: Optional[datetime] = None


class ClientOverviewResponse(BaseModel):
    role: str = "CLIENT"
    entity_name: str
    broker: Optional[BrokerInfo] = None
    active_coverages: list[ClientCoverageEntry] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# /portal/submissions/{code}/{score,peers,actions}
# -----------------------------------------------------------------------------

class ScoreResponse(BaseModel):
    submission_code: str
    coverage: str
    composite_score: Optional[float] = None
    tier: Optional[int] = None
    base_premium: Optional[float] = None
    final_premium: Optional[float] = None
    impact_breakdown: Optional[ImpactBreakdown] = None
    # v8.1: surface loss + exposure summary fields from model_versions so
    # the client portal can render a holistic Risk Insights view without
    # a separate fetch per pillar.
    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    loss_trend_direction: Optional[str] = None
    exposure_value: Optional[float] = None
    exposure_band_label: Optional[str] = None
    exposure_size_score: Optional[float] = None
    exposure_complexity_score: Optional[float] = None
    # v8.1: ROL recommendations so the Scenarios page can render
    # "what if you raised limit to X?" with credible numbers.
    rol_upper_limit: Optional[float] = None
    rol_upper_premium: Optional[float] = None
    rol_lower_limit: Optional[float] = None
    rol_lower_premium: Optional[float] = None


class PeersResponse(BaseModel):
    submission_code: str
    coverage: str
    cohort_id: Optional[str] = None
    cohort_size: Optional[int] = None
    peer_percentile_rank: Optional[float] = None
    cohort_mean_score: Optional[float] = None
    cohort_median_score: Optional[float] = None
    entity_score: Optional[float] = None
    # Phase 2's signal Z-score ranking; populated when feasible
    signal_ranking: Optional[SignalRanking] = None
    note: Optional[str] = None


class ActionsResponse(BaseModel):
    submission_code: str
    coverage: str
    remediation_plan: RemediationPlan


# -----------------------------------------------------------------------------
# /portal/submissions/{code} -- detail with quote history
# -----------------------------------------------------------------------------

class QuoteEvolutionEntry(BaseModel):
    """One quote in the submission's history. Sorted oldest -> newest."""
    quote_code: str
    version_number: int
    composite_score: Optional[float] = None
    tier: Optional[int] = None
    final_premium: Optional[float] = None
    created_at: datetime


class ReferralInfo(BaseModel):
    referral_code: str
    status: str
    awaiting_party: Optional[str] = None


class SubmissionDetailResponse(BaseModel):
    submission_code: str
    entity_name: str
    coverage: str
    status: str
    created_at: datetime
    quotes: list[QuoteEvolutionEntry] = Field(default_factory=list)
    referral: Optional[ReferralInfo] = None


# -----------------------------------------------------------------------------
# /portal/submissions (POST) -- initiate a renewal
# -----------------------------------------------------------------------------

class InitiateSubmissionRequest(BaseModel):
    entity_name: str
    coverage: str
    configuration: Optional[str] = None
    submission_data: Optional[dict] = None
    direct_query_responses: Optional[dict] = None
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = None


class InitiateSubmissionResponse(BaseModel):
    submission_code: str
    status: str


# -----------------------------------------------------------------------------
# /portal/queries (broker inbox)
# -----------------------------------------------------------------------------

class OpenQueryEntry(BaseModel):
    referral_code: str
    submission_code: str
    entity_name: str
    coverage: str
    request_signal_evidence: Optional[str] = None
    open_query_body: Optional[str] = None
    opened_at: Optional[datetime] = None


class BrokerQueriesResponse(BaseModel):
    broker: BrokerInfo
    open_queries: list[OpenQueryEntry] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# /portal/clients/{entity} — broker Client Workbench (revised pack cw_*)
# -----------------------------------------------------------------------------

class ClientWorkbenchModifier(BaseModel):
    """One row in the featured coverage's premium build-up chain."""
    group: str
    factor: Optional[float] = None
    delta: Optional[float] = None
    running: Optional[float] = None


class ClientWorkbenchImpact(BaseModel):
    """One driver in the featured coverage's score impact breakdown."""
    label: str
    delta: float
    direction: str  # "up" | "down"


class ClientWorkbenchMessage(BaseModel):
    """One message in a coverage's referral thread."""
    direction: str  # "carrier" | "broker"
    who: str
    body: str
    at: Optional[datetime] = None
    signal: Optional[str] = None


class ClientWorkbenchThread(BaseModel):
    referral_code: str
    line: str
    carrier: Optional[str] = None
    awaiting: Optional[str] = None
    ask: Optional[str] = None
    messages: list[ClientWorkbenchMessage] = Field(default_factory=list)


class ClientWorkbenchBand(BaseModel):
    label: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    modifier: Optional[float] = None
    active: bool = False


class ClientWorkbenchCoverage(BaseModel):
    """One coverage line in the client workbench (Submission + latest MV +
    Quote + Referral + RiskTerms, flattened to what the tabs render)."""
    code: str
    line: str
    carrier: Optional[str] = None
    score: Optional[float] = None
    pure: Optional[float] = None
    tier: Optional[int] = None
    tier_label: Optional[str] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    percentile: Optional[float] = None
    cohort_median: Optional[float] = None
    cohort_top_decile: Optional[float] = None
    cohort_size: Optional[int] = None
    premium: Optional[float] = None
    recommended: Optional[float] = None
    limit: Optional[float] = None
    deductible: Optional[float] = None
    status: str = "—"
    status_tone: str = "mute"
    signal_coverage: Optional[float] = None
    awaiting: Optional[str] = None
    prev_score: Optional[float] = None
    # Risk terms (Risk Terms tab)
    sir_amount: Optional[float] = None
    sir_applies: Optional[bool] = None
    waiting_period_hours: Optional[float] = None
    aggregate_limit: Optional[float] = None
    reinstatements: Optional[int] = None
    reinstatement_rate: Optional[float] = None
    coverage_trigger: Optional[str] = None
    extensions_count: Optional[int] = None
    exclusions_count: Optional[int] = None
    sub_limits_label: Optional[str] = None
    # Loss + exposure (Score/Loss/Exposure tabs surface the featured line)
    loss_propensity_band: Optional[str] = None
    loss_combined_modifier: Optional[float] = None
    loss_frequency_multiplier: Optional[float] = None
    loss_severity_multiplier: Optional[float] = None
    # F.1: loss trajectory + extra KPIs (CW Loss tab)
    loss_frequency_velocity: Optional[float] = None
    loss_severity_velocity: Optional[float] = None
    loss_confidence: Optional[float] = None
    loss_cohort_name: Optional[str] = None
    loss_trend_direction: Optional[str] = None
    exposure_value: Optional[float] = None
    exposure_band_label: Optional[str] = None
    exposure_size_score: Optional[float] = None
    exposure_complexity_score: Optional[float] = None
    exposure_modifier: Optional[float] = None
    exposure_value_prior: Optional[float] = None
    # F.1: exposure band boundaries (CW Exposure tab)
    exposure_bands: Optional[list[ClientWorkbenchBand]] = None
    # Premium build-up + commercial (Premium tab, featured line)
    base_premium: Optional[float] = None
    net_premium: Optional[float] = None
    gross_premium: Optional[float] = None
    offered_premium: Optional[float] = None
    total_taxes: Optional[float] = None
    total_commission: Optional[float] = None
    brokerage_rate: Optional[float] = None
    distribution_type: Optional[str] = None
    signed_line: Optional[float] = None
    role: Optional[str] = None
    lead_loading_factor: Optional[float] = None
    # F.1: full modifier chain (CW Premium tab)
    modifier_chain: Optional[list[ClientWorkbenchModifier]] = None
    # F.1: score impact breakdown (CW Score tab)
    impact: Optional[list[ClientWorkbenchImpact]] = None
    score_history: Optional[list[ScoreHistoryPoint]] = None


class ClientWorkbenchLossEvent(BaseModel):
    date: Optional[datetime] = None
    line: str
    incurred: Optional[float] = None
    paid: Optional[float] = None
    cause: Optional[str] = None
    status: Optional[str] = None


class ClientWorkbenchResponse(BaseModel):
    # Identity
    entity_name: str
    industry: Optional[str] = None
    naics: Optional[str] = None
    vertical: Optional[str] = None
    revenue_band: Optional[str] = None
    country: Optional[str] = None
    locations: Optional[str] = None
    employees: Optional[str] = None
    domain: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    broker: Optional[str] = None
    # Engagement
    engagement: Optional[float] = None
    engagement_label: Optional[str] = None
    last_message: Optional[str] = None
    avg_response_hours: Optional[float] = None
    open_queries: int = 0
    next_renewal_days: Optional[int] = None
    # Aggregates
    total_premium: float = 0.0
    avg_score: Optional[float] = None
    # Detail
    coverages: list[ClientWorkbenchCoverage] = Field(default_factory=list)
    loss_events: list[ClientWorkbenchLossEvent] = Field(default_factory=list)
    # F.1: referral message threads (CW Communications tab)
    threads: list[ClientWorkbenchThread] = Field(default_factory=list)
