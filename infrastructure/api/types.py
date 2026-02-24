"""
DSI Production API Types (Phase 11)

Request and response models for the REST API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class SubmissionStatus(str, Enum):
    """Submission processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DISCOVERY = "discovery"
    PRICING = "pricing"
    READY = "ready"
    REFERRED = "referred"
    FAILED = "failed"


class QuoteStatus(str, Enum):
    """Quote status."""
    PENDING = "pending"
    READY = "ready"
    REFERRED = "referred"
    EXPIRED = "expired"
    BOUND = "bound"
    DECLINED = "declined"


class ReferralDecisionType(str, Enum):
    """Referral decision types."""
    APPROVE = "approve"
    DECLINE = "decline"
    MODIFY = "modify"


class Permission(str, Enum):
    """API permissions."""
    SUBMIT = "submit"
    QUOTE = "quote"
    REFERRAL = "referral"
    ANALYTICS = "analytics"
    ADMIN = "admin"


# =============================================================================
# SUBMISSION MODELS
# =============================================================================

class SubmissionRequest(BaseModel):
    """Request to create a new submission."""
    entity_name: str = Field(..., description="Name of the entity to price")
    domain_hint: Optional[str] = Field(None, description="Optional domain hint for discovery")
    country_hint: Optional[str] = Field(None, description="Optional country/locale hint (e.g., US, UK, DE)")
    coverage: str = Field(..., description="Coverage type (e.g., fi, cyber, do)")
    configuration: Optional[str] = Field(None, description="Specific configuration to use")

    # Optional submission data
    submission_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Traditional pricing inputs (TIV, revenue, etc.)"
    )

    # Direct query responses
    direct_query_responses: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pre-answered direct query responses"
    )

    # Options
    async_mode: bool = Field(False, description="Run asynchronously")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion")


class SubmissionResponse(BaseModel):
    """Response after creating a submission."""
    submission_id: str
    status: SubmissionStatus
    estimated_completion: Optional[datetime] = None
    job_id: Optional[str] = None


class SubmissionDetail(BaseModel):
    """Detailed submission information."""
    submission_id: str
    entity_name: str
    domain: Optional[str] = None
    coverage: str
    configuration: str
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    quote_id: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# QUOTE MODELS
# =============================================================================

class PremiumOption(BaseModel):
    """Premium option at a limit."""
    limit: float
    premium: float
    rate: float


class SignalSummary(BaseModel):
    """Summary of signal outputs."""
    total_signals: int
    signals_extracted: int
    top_factors: List[Dict[str, Any]]


class DiscoverySummary(BaseModel):
    """Discovery result summary."""
    domain: str
    confidence: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None


class QuoteResponse(BaseModel):
    """Quote response with pricing details."""
    quote_id: str
    submission_id: str
    status: QuoteStatus

    # Scoring
    composite_score: int
    tier: int
    tier_label: str
    decision: str  # approve, refer, decline

    # Premium options
    premium_options: Dict[str, float] = Field(
        default_factory=dict,
        description="Premium by limit"
    )
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None

    # Details
    discovery: Optional[DiscoverySummary] = None
    signal_summary: Optional[SignalSummary] = None

    # Referral info
    referral_reasons: List[str] = Field(default_factory=list)
    referral_id: Optional[str] = None

    # Validity
    valid_until: Optional[datetime] = None
    created_at: datetime


class QuoteListItem(BaseModel):
    """Quote in a list."""
    quote_id: str
    submission_id: str
    entity_name: str
    coverage: str
    status: QuoteStatus
    tier: int
    premium: float
    created_at: datetime


# =============================================================================
# REFERRAL MODELS
# =============================================================================

class ReferralDecision(BaseModel):
    """Referral decision request."""
    decision: ReferralDecisionType
    adjustments: Optional[Dict[str, Any]] = None
    notes: List[str] = Field(default_factory=list)
    underwriter_id: Optional[str] = None


class ReferralDetail(BaseModel):
    """Referral information."""
    referral_id: str
    quote_id: str
    submission_id: str
    entity_name: str
    coverage: str

    # Status
    status: str  # pending, approved, declined
    reasons: List[str]

    # Original quote
    original_tier: int
    original_score: int
    original_premium: float

    # Resolution
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: List[str] = Field(default_factory=list)

    # Adjustments applied
    tier_override: Optional[int] = None
    premium_adjustment: Optional[float] = None

    created_at: datetime


class ReferralListItem(BaseModel):
    """Referral in a list."""
    referral_id: str
    entity_name: str
    coverage: str
    status: str
    reasons: List[str]
    age_hours: float
    created_at: datetime


# =============================================================================
# MULTI-COVERAGE MODELS
# =============================================================================

class MultiCoverageRequest(BaseModel):
    """Request for multi-coverage pricing."""
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = Field(None, description="Optional country/locale hint (e.g., US, UK, DE)")
    coverages: Optional[List[str]] = Field(None, description="Coverages to price (None = auto)")
    locales: Optional[List[str]] = Field(None, description="Locales to test (None = auto)")
    submission_data: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = True
    require_approval_above: int = 50


class MultiCoverageResponse(BaseModel):
    """Response for multi-coverage pricing."""
    result_id: str
    entity_name: str
    detected_locale: Optional[str] = None

    # Per-coverage results
    coverage_quotes: Dict[str, QuoteResponse] = Field(default_factory=dict)
    failed_coverages: List[str] = Field(default_factory=list)

    # Package info
    recommended_package: List[str] = Field(default_factory=list)
    package_discount: float = 0.0
    combined_premium: float = 0.0
    total_savings: float = 0.0

    # Metrics
    duration_seconds: float = 0.0
    cache_hit_rate: float = 0.0


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary analytics."""
    as_of_date: datetime
    coverage: Optional[str] = None
    period: str

    # Volume
    total_submissions: int
    total_quotes: int
    total_binds: int
    total_declines: int

    # Premium
    gross_written_premium: float
    quoted_premium: float
    average_premium: float

    # Risk metrics
    average_score: float
    average_tier: float
    tier_distribution: Dict[int, int]

    # Rates
    quote_rate: float
    bind_rate: float
    decline_rate: float


class TurnaroundMetricsResponse(BaseModel):
    """Workflow turnaround metrics."""
    period: str
    sample_size: int

    avg_time_to_quote: float
    avg_time_to_decision: float
    p50_time_to_quote: float
    p90_time_to_quote: float
    p95_time_to_quote: float

    sla_target_hours: float
    sla_compliance_rate: float

    time_by_tier: Dict[int, float]


class SignalHealthResponse(BaseModel):
    """Signal health metrics."""
    coverage: str
    period: str

    overall_coverage: float
    group_coverage: Dict[str, float]
    signal_coverage: Dict[str, float]

    issues: List[Dict[str, Any]]


# =============================================================================
# JOB MODELS
# =============================================================================

class JobStatus(str, Enum):
    """Async job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Async job status response."""
    job_id: str
    status: JobStatus
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# AUTH MODELS
# =============================================================================

class TokenRequest(BaseModel):
    """Token request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    permissions: List[str]


class APIKeyValidation(BaseModel):
    """API key validation result."""
    valid: bool
    client_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    rate_limit_tier: str = "standard"


# =============================================================================
# HEALTH & CONFIG MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str] = Field(default_factory=dict)


class ConfigResponse(BaseModel):
    """Configuration response."""
    coverages: List[str]
    locales: List[str]
    rate_limits: Dict[str, int]
    features: Dict[str, bool]


# =============================================================================
# LIST/PAGINATION MODELS
# =============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class ListFilters(BaseModel):
    """Common list filters."""
    coverage: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


# =============================================================================
# PHASE 8: SIGNAL OVERRIDE MODELS (Deterministic Referral Management)
# =============================================================================

class SignalValue(BaseModel):
    """
    Signal value container for Phase 8 audit trail.

    Contains both the machine-inferred value (permanent) and
    optionally a human-audited override (mutable).
    """
    signal_id: str
    inferred_value: float = Field(..., description="Machine-inferred score (permanent)")
    audited_value: Optional[float] = Field(None, description="Human-audited override (mutable)")
    is_overridden: bool = False
    confidence: float = 1.0

    @property
    def effective_value(self) -> float:
        """Return audited_value if overridden, else inferred_value."""
        return self.audited_value if self.is_overridden and self.audited_value is not None else self.inferred_value


class SignalOverrideRequest(BaseModel):
    """
    Request to override a signal value during referral review.

    Per Phase 8: Underwriters audit inputs (signals), not outputs (premiums).
    This creates an audit trail with rationale and evidence.
    """
    signal_id: str = Field(..., description="ID of the signal to override")
    audited_value: float = Field(..., ge=0, le=100, description="Corrected signal value (0-100)")
    rationale: str = Field(..., min_length=10, description="Explanation for the override")
    evidence_reference: Optional[str] = Field(None, description="Reference to supporting evidence (URL, doc ID)")
    underwriter_id: Optional[str] = Field(None, description="ID of underwriter making the override")


class SignalOverrideResponse(BaseModel):
    """Response after applying a signal override."""
    signal_id: str
    entity_id: str
    model_version_id: str

    # Values
    inferred_value: float = Field(..., description="Original machine value (preserved)")
    audited_value: float = Field(..., description="New audited value")

    # Impact
    score_impact: float = Field(..., description="Change to composite score")
    tier_impact: int = Field(..., description="Change to tier (0 if unchanged)")
    new_composite_score: float
    new_tier: int
    new_tier_label: str

    # Audit
    overridden_by: str
    overridden_at: datetime
    rationale: str
    evidence_reference: Optional[str] = None

    # Model versioning
    previous_model_version: str
    new_model_version: str


class ModelVersionResponse(BaseModel):
    """
    Model version snapshot for Phase 8 audit trail.

    v1 = machine view (inferred_value only)
    v2+ = human-audited view (with audited_value overrides)
    """
    version_id: str
    version_number: int
    version_type: str  # "initial", "signal_override", "referral_review"

    # Scoring
    composite_score: float
    tier: int
    tier_label: str
    confidence: float

    # Signals
    signal_count: int
    overridden_signals: List[str] = Field(default_factory=list)

    # Audit
    created_by: str
    created_at: datetime
    notes: List[str] = Field(default_factory=list)


class ReferralSignalsRequest(BaseModel):
    """Request to get signals for a referral (for underwriter review)."""
    include_all: bool = Field(False, description="Include all signals, not just flagged ones")
    include_raw_data: bool = Field(False, description="Include raw extraction data")


class ReferralSignalDetail(BaseModel):
    """Detailed signal information for referral review."""
    signal_id: str
    signal_name: str
    group_id: str
    group_name: str

    # Values
    inferred_value: float
    audited_value: Optional[float] = None
    is_overridden: bool = False

    # Impact
    weight: float
    contribution_to_score: float

    # Status
    is_flagged: bool = False
    flag_reason: Optional[str] = None

    # Metadata
    confidence: float
    data_sources: List[str] = Field(default_factory=list)
    extracted_at: datetime

    # Raw data (if requested)
    raw_data: Optional[Dict[str, Any]] = None


class ReferralSignalsResponse(BaseModel):
    """Response containing signals for referral review."""
    referral_id: str
    model_version_id: str

    # Signals
    signals: List[ReferralSignalDetail]
    flagged_count: int
    overridden_count: int

    # Summary
    total_signals: int
    signal_coverage: float
    average_confidence: float


# =============================================================================
# SIMULATION TYPES (Phase 3)
# =============================================================================

class ShockParameterRequest(BaseModel):
    """Shock parameter for portfolio simulation."""
    signal_id: str = Field(..., description="Signal to shock")
    shock_type: str = Field(
        "multiplier",
        description="Shock type: override, multiplier, additive, percentile",
    )
    value: float = Field(..., description="Shock value (e.g., 0.5 for 50% multiplier)")
    industry_filter: Optional[str] = Field(None, description="Filter by industry")
    tier_filter: Optional[int] = Field(None, description="Filter by tier")
    coverage_filter: Optional[str] = Field(None, description="Filter by coverage")


class SimulateRequest(BaseModel):
    """Request to run a portfolio stress-test simulation."""
    portfolio_json: str = Field(
        ...,
        description="JSON string of portfolio snapshot (entities with signals)",
    )
    shocks: List[ShockParameterRequest] = Field(
        ...,
        min_length=1,
        description="One or more shock parameters to apply",
    )
    config_path: Optional[str] = Field(
        None, description="Path to coverage YAML config for the simulator"
    )
    iterations: int = Field(
        1, ge=1, le=100_000,
        description="Number of simulation iterations (1 = deterministic)",
    )


class TierMigration(BaseModel):
    """Tier migration summary for a single entity."""
    entity_id: str
    old_tier: int
    new_tier: int


class SimulationStats(BaseModel):
    """Statistical summary of simulation results."""
    mean_score_delta: float
    std_score_delta: float
    entities_upgraded: int
    entities_downgraded: int
    max_premium_increase_pct: float = 0.0
    max_premium_decrease_pct: float = 0.0


class SimulateResponse(BaseModel):
    """Response from portfolio simulation."""
    simulation_id: str
    status: str = "completed"

    # Headline metrics
    premium_adequacy: float = Field(
        description="Post-shock / pre-shock total premium ratio"
    )
    total_premium_impact: float = Field(
        description="Absolute change in total portfolio premium"
    )
    entities_affected: int = Field(
        description="Number of entities whose premium changed"
    )
    total_entities: int = Field(
        description="Total entities in portfolio"
    )

    # Tier migration
    tier_migrations: List[TierMigration] = Field(default_factory=list)

    # Statistics
    stats: SimulationStats

    # Metadata
    execution_time_ms: float
    created_at: datetime
