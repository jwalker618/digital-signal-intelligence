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


class BrokerOverviewResponse(BaseModel):
    role: str = "BROKER"
    broker: BrokerInfo
    clients: list[ClientBookEntry] = Field(default_factory=list)
    open_queries_count: int = 0


class ClientCoverageEntry(BaseModel):
    submission_code: str
    coverage: str
    composite_score: Optional[float] = None
    tier: Optional[int] = None
    peer_percentile_rank: Optional[float] = None
    recommended_premium: Optional[float] = None
    referral_state: Optional[str] = None
    updated_at: Optional[datetime] = None


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
